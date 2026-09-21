"""Quantize every float ONNX file of an export to int8, and keep them.

    python3 -m deploy.quantize runs_repo revision onnx/<time> runs_dir local_dir [--rebuild]
"""

from __future__ import annotations

import os
import platform
import tempfile

import numpy as np
import onnx
import onnxruntime
from onnxruntime.quantization import (CalibrationDataReader, CalibrationMethod,
                                      QuantFormat, QuantType, quantize_static)
from onnxruntime.quantization.shape_inference import quant_pre_process

from assemble.train_set import fetch_train_set
from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import Settings
from deploy.export import file_of
from evaluate.calibrate import calibration_rows
from evaluate.fit import rows_to_fit
from models.fits import model_from


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


def write_int8_files(names, source, rows, dest, batch):
    """Quantize each `name`'s float file in `source` to int8 in `dest`, on `rows`."""
    os.makedirs(dest, exist_ok=True)
    for name in names:
        with tempfile.TemporaryDirectory() as scratch:
            prepared = os.path.join(scratch, f"{name}_prepared.onnx")
            quant_pre_process(os.path.join(source, f"{name}_float.onnx"), prepared)
            quantize_static(prepared, os.path.join(dest, f"{name}_int8.onnx"),
                            Rows(rows, "row", batch), quant_format=QuantFormat.QDQ,
                            per_channel=True, activation_type=QuantType.QInt8,
                            weight_type=QuantType.QInt8,
                            calibrate_method=CalibrationMethod.MinMax)


def int8_thresholds(exported, calibration, folder, target):
    """Calibrate each int8 model again on the calibration rows."""
    kept = []
    for entry in exported:
        scores = onnx_residuals(
            os.path.join(folder, f"{file_of(model_from(entry))}_int8.onnx"), calibration)
        kept.append({**entry, "int8_threshold": threshold_for(scores, target)})
    return kept


def write_quantized(folder, runs_repo, revision, onnx_path, runs_dir, local_dir,
                    settings):
    """Write each float file of an export as int8, and return what to record.

    The int8 file is quantized on the rows the model was fitted on.
    """
    source, exported = read_dir(runs_repo, onnx_path, runs_dir, revision)
    at = exported["train_set"]
    train_set = fetch_train_set(at["repo"], at["revision"], at["path"], local_dir)

    write_int8_files([file_of(model_from(entry)) for entry in exported["exported"]],
                     source, rows_to_fit(train_set), folder, settings.BATCH)
    calibration = calibration_rows(train_set, settings)
    thresholds = int8_thresholds(exported["exported"], calibration, folder,
                                 settings.TARGET)
    return {"onnx": {"repo": runs_repo, "revision": revision, "path": onnx_path},
            **{name: exported[name] for name in ("models", "train_set", "split", "grid")},
            "thresholds": thresholds,
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "onnx": onnx.__version__,
                         "onnxruntime": onnxruntime.__version__}}


def main(runs_repo, revision, onnx_path, runs_dir, local_dir, rebuild=False):
    settings = Settings()
    inputs = {"onnx": onnx_path, "target": settings.TARGET, "batch": settings.BATCH}
    return reuse_or_make(runs_repo, "quantize", inputs, runs_dir,
                         lambda folder: write_quantized(folder, runs_repo, revision,
                                                        onnx_path, runs_dir, local_dir,
                                                        settings),
                         rebuild)


if __name__ == "__main__":
    main(**arguments(("runs_repo", "revision", "onnx_path", "runs_dir", "local_dir"),
                    rebuild=False))
