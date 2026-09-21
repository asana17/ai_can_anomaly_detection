"""Write every nonlinear autoencoder of a fit out as float and int8 ONNX, and keep them.

    python3 -m quantize.export runs_repo revision models/<time> runs_dir local_dir [--rebuild]
"""

from __future__ import annotations

import json
import os
import platform
import tempfile

import numpy as np
import onnx
import onnxruntime
import torch
from onnxruntime.quantization import (CalibrationDataReader, CalibrationMethod,
                                      QuantFormat, QuantType, quantize_static)
from onnxruntime.quantization.shape_inference import quant_pre_process

from assemble.train_set import fetch_train_set
from common.cli import arguments
from common.hub_dirs import reuse_or_make
from common.settings import Settings
from evaluate.calibrate import calibration_rows
from evaluate.fit import fetch_models, rows_to_fit
from models.fits import NonlinearAe, as_dict, models_from


class Rows(CalibrationDataReader):
    """Feeds the training rows to the quantizer, `batch` at a time."""

    def __init__(self, rows, name, batch):
        self.batches = iter(np.array_split(rows, max(len(rows) // batch, 1)))
        self.name = name

    def get_next(self):
        batch = next(self.batches, None)
        return None if batch is None else {self.name: batch.astype(np.float32)}


def onnx_residuals(path, rows, batch=8192):
    """Each row's mean squared reconstruction error from the ONNX file at `path`."""
    session = onnxruntime.InferenceSession(path, providers=["CPUExecutionProvider"])
    out = []
    for fed in np.array_split(np.asarray(rows, dtype=np.float32),
                              max(len(rows) // batch, 1)):
        got = session.run(None, {"row": fed})[0]
        out.append(((got - fed) ** 2).mean(axis=1))
    return np.concatenate(out)


def threshold_for(scores, target):
    """The score that cuts `target` of the calibration rows off."""
    return float(np.percentile(scores, 100 * (1 - target)))


def write_onnx_files(models, rows, dest, batch):
    """Write each model into `dest` as float ONNX, and as int8 quantized on `rows`."""
    os.makedirs(dest, exist_ok=True)
    for name, model in models:
        float_path = os.path.join(dest, f"{name}_float.onnx")
        model.eval()
        torch.onnx.export(model, torch.zeros(1, rows.shape[1]), float_path, dynamo=False,
                          input_names=["row"], output_names=["out"],
                          dynamic_axes={"row": {0: "batch"}, "out": {0: "batch"}})
        with tempfile.TemporaryDirectory() as scratch:
            prepared = os.path.join(scratch, f"{name}_prepared.onnx")
            quant_pre_process(float_path, prepared)
            quantize_static(prepared, os.path.join(dest, f"{name}_int8.onnx"),
                            Rows(rows, "row", batch), quant_format=QuantFormat.QDQ,
                            per_channel=True, activation_type=QuantType.QInt8,
                            weight_type=QuantType.QInt8,
                            calibrate_method=CalibrationMethod.MinMax)


def file_of(model):
    """What the ONNX files of `model` are named."""
    return f"nonlinear_ae_k{model.k}_h{model.hidden}"


def int8_thresholds(models, calibration, folder, target):
    """Calibrate each int8 model again on the calibration rows."""
    kept = []
    for model in models:
        scores = onnx_residuals(os.path.join(folder, f"{file_of(model)}_int8.onnx"),
                                calibration)
        kept.append({**as_dict(model),
                     "int8_threshold": threshold_for(scores, target)})
    return kept


def write_export(folder, runs_repo, revision, models_path, runs_dir, local_dir,
                 settings):
    """Write each nonlinear autoencoder of a fit as ONNX, and return what to record.

    The float file is the model as it was fitted. The int8 file is quantized on the
    rows the model was fitted on.
    """
    weights, models_meta = fetch_models(runs_repo, revision, models_path, runs_dir)
    at = models_meta["train_set"]
    train_set = fetch_train_set(at["repo"], at["revision"], at["path"], local_dir)
    rows = rows_to_fit(train_set)
    calibration = calibration_rows(train_set, settings)

    # the board runs a nonlinear autoencoder, so the other models are left out
    wanted = [model for model in models_from(models_meta["inputs"]["models"])
              if isinstance(model, NonlinearAe)]
    write_onnx_files([(file_of(model),
                       model.network_with_weights(weights, rows.shape[1]))
                      for model in wanted], rows, folder, settings.BATCH)
    thresholds = int8_thresholds(wanted, calibration, folder, settings.TARGET)
    return {"models": {"repo": runs_repo, "revision": revision, "path": models_path},
            **{name: models_meta[name] for name in ("train_set", "split", "grid")},
            "thresholds": thresholds,
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "onnx": onnx.__version__,
                         "onnxruntime": onnxruntime.__version__}}


def main(runs_repo, revision, models_path, runs_dir, local_dir, rebuild=False):
    settings = Settings()
    inputs = {"models": models_path, "target": settings.TARGET,
              "batch": settings.BATCH}
    return reuse_or_make(runs_repo, "quantize", inputs, runs_dir,
                         lambda folder: write_export(folder, runs_repo, revision,
                                                     models_path, runs_dir, local_dir,
                                                     settings),
                         rebuild)


if __name__ == "__main__":
    main(*arguments(("runs_repo", "revision", "models_path", "runs_dir", "local_dir"),
                    rebuild=False))
