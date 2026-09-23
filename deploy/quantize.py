"""Quantize every float ONNX file of an export to int8.

    python3 -m deploy.quantize runs_repo revision onnx/<time> runs_dir local_dir [--rebuild] [--settings <file>]
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
from common.settings import read_settings
from models.fit import fetch_fitted_models
from models.fits import model_from
from models.onnx_files import onnx_name
from models.torch_files import scale_of


class Rows(CalibrationDataReader):
    """Feeds the training rows to the quantizer, `batch` at a time."""

    def __init__(self, rows, name, batch):
        self.batches = iter(np.array_split(rows, max(len(rows) // batch, 1)))
        self.name = name

    def get_next(self):
        batch = next(self.batches, None)
        return None if batch is None else {self.name: batch.astype(np.float32)}


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


def batch_for(models, settings):
    """The batch the quantizer feeds rows at, `BATCH`, checked against the fit.

    It stops when an autoencoder was fitted at another batch, since `BATCH` is that
    one value and the fit reads its own from the `--models` file.
    """
    fitted = {entry["batch"] for entry in models if "batch" in entry}
    if fitted - {settings.BATCH}:
        raise ValueError(f"the models were fitted at batch {sorted(fitted)}, "
                         f"and BATCH is {settings.BATCH}")
    return settings.BATCH


def write_quantized(folder, runs_repo, revision, onnx_path, runs_dir, local_dir,
                    settings):
    """Write each float file of an export as int8, and return what to record.

    The int8 file is quantized on the rows the model was fitted on.
    """
    source, exported = read_dir(runs_repo, onnx_path, runs_dir, revision)
    at = exported["train_set"]
    train_set = fetch_train_set(at["repo"], at["revision"], at["path"], local_dir)
    models = exported["models"]
    weights, fitted = fetch_fitted_models(runs_repo, models["revision"],
                                          models["path"], runs_dir)
    rows = scale_of(weights).apply(train_set["train"])

    write_int8_files([onnx_name(model_from(entry)) for entry in exported["exported"]],
                     source, rows, folder,
                     batch_for(fitted["inputs"]["models"], settings))
    return {"onnx": {"repo": runs_repo, "revision": revision, "path": onnx_path},
            **{name: exported[name]
               for name in ("models", "train_set", "log_split", "grid")},
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "onnx": onnx.__version__,
                         "onnxruntime": onnxruntime.__version__}}


def main(runs_repo, revision, onnx_path, runs_dir, local_dir, rebuild=False,
         dry_run=False, settings=None):
    settings = read_settings(settings)
    inputs = {"onnx": onnx_path}
    return reuse_or_make(runs_repo, "quantize", inputs, runs_dir,
                         lambda folder: write_quantized(folder, runs_repo, revision,
                                                        onnx_path, runs_dir, local_dir,
                                                        settings),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("runs_repo", "revision", "onnx_path", "runs_dir", "local_dir"),
                    rebuild=False, settings=None))
