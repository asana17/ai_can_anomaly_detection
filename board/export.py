"""Write every nonlinear autoencoder of a run out as float and int8 ONNX, and keep them.

    python3 -m board.export "data/part_*/*.csv" out runs_clone started
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

from assemble.split import moving, split
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


def fits_in(run_dir):
    """The `k` and `h` of every nonlinear autoencoder the run saved."""
    weights = load_file(os.path.join(run_dir, "weights.safetensors"))
    got = {tuple(int(part[1:]) for part in name.split(".")[1:3])
           for name in weights if name.startswith("nonlinear_ae.")}
    return sorted((k, h) for h, k in got)


def write(models, rows, dest, batch):
    """Write each model into a new `dest` as float ONNX, and as int8 quantized on `rows`."""
    os.makedirs(dest)                       # raises rather than overwrite an export
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


def main(pattern, out_dir, runs_clone, started):
    settings = Settings()
    exported = time.localtime()
    stamp = time.strftime("%Y%m%d-%H%M%S", exported)
    commit = git("rev-parse", "HEAD").strip()
    uncommitted = git("status", "--porcelain").splitlines()
    run = os.path.join("results", started)
    run_dir = os.path.join(runs_clone, run)
    wanted = fits_in(run_dir)               # every fit the run saved, none of them picked
    # the weights are read before the rows, which take long
    states = [(k, h, load(run_dir, k, h)) for k, h in wanted]

    logs = sorted(glob.glob(pattern))
    train_logs, _ = split(seconds_for(logs, out_dir, settings), settings.TRAIN)
    data, _ = arrays_for(train_logs, out_dir, settings)
    above = moving(data["scale"].undo(data["rows"]), settings.MIN_SPEED)
    tr = data["rows"][above]                # the same training rows as evaluate.pc.run

    models = []
    for k, h, state in states:
        model = NonlinearAutoencoder(signals=tr.shape[1], latent_dim=k, hidden=h)
        model.load_state_dict(state)
        models.append((f"nonlinear_ae_k{k}_h{h}", model))
    path = os.path.join("board", stamp)
    dest = os.path.join(runs_clone, path)
    write(models, tr, dest, settings.BATCH)

    meta = {"run": run, "models": [{"k": k, "h": h} for k, h in wanted],
            "commit": commit, "uncommitted": uncommitted,
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "onnx": onnx.__version__,
                         "onnxruntime": onnxruntime.__version__},
            "exported": time.strftime("%Y-%m-%dT%H:%M:%S%z", exported)}
    with open(os.path.join(dest, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    git("-C", runs_clone, "add", path)
    git("-C", runs_clone, "commit", "-m",
        f"add {path} from {run}, {len(wanted)} models")
    git("-C", runs_clone, "push")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
