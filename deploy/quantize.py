"""Quantize every float ONNX file of an export to int8.

    python3 -m deploy.quantize runs_repo revision onnx/<time> runs_dir local_dir [--rebuild]

`onnx/<time>` can be `window_onnx/<time>` too, and the int8 files then go to
`window_quantize/<time>`.
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
from common.settings import QuantizeSettings
from models.fit import fetch_fitted_models
from models.fits import model_from
from models.torch_files import scale_of
from preprocess.features.moving import moving
from preprocess.features.windows import complete_window_ends, window_rows

# where the int8 files go, by the kind of export they are quantized from
KINDS = {"onnx": "quantize", "window_onnx": "window_quantize"}


class Rows(CalibrationDataReader):
    """Feeds the quantizer `batches`, each a batch of the model's input rows."""

    def __init__(self, batches, name):
        self.batches = iter(batches)
        self.name = name

    def get_next(self):
        batch = next(self.batches, None)
        return None if batch is None else {self.name: batch.astype(np.float32)}


def write_int8_file(name, source, batches, dest):
    """Quantize `name`'s float file in `source` to int8 in `dest`, on `batches`."""
    os.makedirs(dest, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        prepared = os.path.join(scratch, f"{name}_prepared.onnx")
        quant_pre_process(os.path.join(source, f"{name}_float.onnx"), prepared)
        quantize_static(prepared, os.path.join(dest, f"{name}_int8.onnx"),
                        Rows(batches, "row"), quant_format=QuantFormat.QDQ,
                        per_channel=True, activation_type=QuantType.QInt8,
                        weight_type=QuantType.QInt8,
                        calibrate_method=CalibrationMethod.MinMax)


def write_int8_files(names, source, rows, dest, batch):
    """Quantize each `name`'s float file in `source` to int8 in `dest`, on `rows`,
    `batch` rows or a few more at a time."""
    for name in names:
        write_int8_file(name, source, np.array_split(rows, max(len(rows) // batch, 1)),
                        dest)


def write_window_int8_files(models, source, raw, rows, moved, segment, dest, batch):
    """Quantize each window model's float file in `source` to int8 in `dest`, on the
    windows of `rows` it was fitted on, `batch` windows or a few more at a time.

    `raw` is the train set before it was scaled into `rows`, `moved` its moving rows and
    `segment` its segment ids. A window goes in as one row, its oldest row first, as
    `export_windows` writes it."""
    for model in models:
        ends = complete_window_ends(raw, moved, segment, rows=model.rows,
                                    stride=getattr(model, "stride", 1))
        batches = (window_rows(rows, part, rows=model.rows).reshape(len(part), -1)
                   for part in np.array_split(ends, max(len(ends) // batch, 1)))
        write_int8_file(model.onnx_name, source, batches, dest)


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

    The int8 file is quantized on the rows, or the windows, the model was fitted on.
    """
    source, exported = read_dir(runs_repo, onnx_path, runs_dir, revision)
    at = exported["train_set"]
    train_set = fetch_train_set(at["repo"], at["revision"], at["path"], local_dir)
    models = exported["models"]
    weights, fitted = fetch_fitted_models(runs_repo, models["revision"],
                                          models["path"], runs_dir)
    batch = batch_for(fitted["inputs"]["models"], settings)
    wanted = [model_from(entry) for entry in exported["exported"]]
    raw = train_set["train"]
    if onnx_path.startswith("window_onnx/"):
        write_window_int8_files(wanted, source, raw, scale_of(weights).apply(raw),
                                moving(raw, min_speed=train_set["min_speed"]),
                                train_set["seg"], folder, batch)
    else:
        # fit drops a row that holds a NaN, a value J1939 reserves
        rows = scale_of(weights).apply(raw[~np.isnan(raw).any(axis=1)])
        write_int8_files([model.onnx_name for model in wanted], source, rows, folder,
                         batch)
    return {"onnx": {"repo": runs_repo, "revision": revision, "path": onnx_path},
            **{name: exported[name]
               for name in ("models", "train_set", "log_split", "grid")},
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "onnx": onnx.__version__,
                         "onnxruntime": onnxruntime.__version__}}


def main(runs_repo, revision, onnx_path, runs_dir, local_dir, rebuild=False,
         dry_run=False, settings=QuantizeSettings()):
    exported_kind = onnx_path.split("/")[0]
    if exported_kind not in KINDS:
        raise ValueError(f"{onnx_path} is not under {' or '.join(KINDS)}")
    return reuse_or_make(runs_repo, KINDS[exported_kind], {"onnx": onnx_path}, {},
                         runs_dir,
                         lambda folder: write_quantized(folder, runs_repo, revision,
                                                        onnx_path, runs_dir, local_dir,
                                                        settings),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("runs_repo", "revision", "onnx_path", "runs_dir", "local_dir"),
                    rebuild=False))
