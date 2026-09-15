"""Write one nonlinear autoencoder from a run out as float and int8 ONNX, and keep them.

    python3 -m board.export "data/part_*/*.csv" out runs_clone started k h
"""

from __future__ import annotations

import glob
import json
import os
import platform
import sys
import tempfile
import time

import numpy as np
import onnx
import onnxruntime
import torch
from onnxruntime.quantization import (CalibrationDataReader, CalibrationMethod,
                                      QuantFormat, QuantType, quantize_static)
from onnxruntime.quantization.shape_inference import quant_pre_process
from safetensors.torch import load_file

from assemble.split import WHEEL, split
from evaluate.pc.record import git
from evaluate.pc.run import Settings, arrays_for, seconds_for
from models.autoencoder import NonlinearAutoencoder


class Rows(CalibrationDataReader):
    """Feeds the training rows to the quantizer, `batch` at a time."""

    def __init__(self, rows, name, batch):
        self.batches = iter(np.array_split(rows, max(len(rows) // batch, 1)))
        self.name = name

    def get_next(self):
        batch = next(self.batches, None)
        return None if batch is None else {self.name: batch.astype(np.float32)}


def load(run_dir, k, h):
    """The `state_dict` of the run's nonlinear autoencoder at `k` and `h`."""
    prefix = f"nonlinear_ae.h{h}.k{k}."
    weights = load_file(os.path.join(run_dir, "weights.safetensors"))
    state = {name[len(prefix):]: tensor for name, tensor in weights.items()
             if name.startswith(prefix)}
    if not state:
        raise ValueError(f"{run_dir} holds no nonlinear autoencoder at k={k} h={h}")
    return state


def write(model, rows, dest, name, batch):
    """Write `model` into a new `dest` as float ONNX, and as int8 quantized on `rows`."""
    os.makedirs(dest)                       # raises rather than overwrite an export
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


def main(pattern, out_dir, runs_clone, started, k, h):
    settings = Settings()
    exported = time.localtime()
    stamp = time.strftime("%Y%m%d-%H%M%S", exported)
    commit = git("rev-parse", "HEAD").strip()
    uncommitted = git("status", "--porcelain").splitlines()
    run = os.path.join("results", started)
    state = load(os.path.join(runs_clone, run), k, h)   # before the rows, which take long

    logs = sorted(glob.glob(pattern))
    train_logs, _ = split(seconds_for(logs, out_dir, settings), settings.TRAIN)
    data, _ = arrays_for(train_logs, out_dir, settings)
    moving = data["scale"].undo(data["rows"])[:, WHEEL] > settings.MIN_SPEED
    tr = data["rows"][moving]               # the same training rows as evaluate.pc.run

    model = NonlinearAutoencoder(signals=tr.shape[1], latent_dim=k, hidden=h)
    model.load_state_dict(state)
    path = os.path.join("board", stamp)
    dest = os.path.join(runs_clone, path)
    write(model, tr, dest, f"nonlinear_ae_k{k}_h{h}", settings.BATCH)

    meta = {"run": run, "k": k, "h": h,
            "commit": commit, "uncommitted": uncommitted,
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "onnx": onnx.__version__,
                         "onnxruntime": onnxruntime.__version__},
            "exported": time.strftime("%Y-%m-%dT%H:%M:%S%z", exported)}
    with open(os.path.join(dest, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    git("-C", runs_clone, "add", path)
    git("-C", runs_clone, "commit", "-m", f"add {path} from {run} k={k} h={h}")
    git("-C", runs_clone, "push")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]),
         int(sys.argv[6]))
