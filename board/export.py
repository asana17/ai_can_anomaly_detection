"""Write one nonlinear autoencoder from a run out as float and int8 ONNX.

    python3 -m board.export "data/part_*/*.csv" out run_dir k h dest
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np
import torch
from onnxruntime.quantization import (CalibrationDataReader, CalibrationMethod,
                                      QuantFormat, QuantType, quantize_static)
from onnxruntime.quantization.shape_inference import quant_pre_process
from safetensors.torch import load_file

from assemble.split import WHEEL, split
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


def main(pattern, out_dir, run_dir, k, h, dest):
    settings = Settings()
    os.makedirs(dest, exist_ok=True)
    logs = sorted(glob.glob(pattern))
    train_logs, _ = split(seconds_for(logs, out_dir, settings), settings.TRAIN)
    data, _ = arrays_for(train_logs, out_dir, settings)
    moving = data["scale"].undo(data["rows"])[:, WHEEL] > settings.MIN_SPEED
    tr = data["rows"][moving]               # the same training rows as evaluate.pc.run

    prefix = f"nonlinear_ae.h{h}.k{k}."
    weights = load_file(os.path.join(run_dir, "weights.safetensors"))
    model = NonlinearAutoencoder(signals=tr.shape[1], latent_dim=k, hidden=h)
    model.load_state_dict({name[len(prefix):]: tensor for name, tensor in weights.items()
                           if name.startswith(prefix)})

    name = f"nonlinear_ae_k{k}_h{h}"
    float_path = os.path.join(dest, f"{name}_float.onnx")
    model.eval()
    torch.onnx.export(model, torch.zeros(1, tr.shape[1]), float_path, dynamo=False,
                      input_names=["row"], output_names=["out"],
                      dynamic_axes={"row": {0: "batch"}, "out": {0: "batch"}})

    prepared = os.path.join(dest, f"{name}_prepared.onnx")
    quant_pre_process(float_path, prepared)
    quantize_static(prepared, os.path.join(dest, f"{name}_int8.onnx"),
                    Rows(tr, "row", settings.BATCH), quant_format=QuantFormat.QDQ,
                    per_channel=True, activation_type=QuantType.QInt8,
                    weight_type=QuantType.QInt8, calibrate_method=CalibrationMethod.MinMax)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]),
         sys.argv[6])
