"""What a model's ONNX files are named, and how rows are scored with one."""

from __future__ import annotations

import os
from functools import partial

import numpy as np
import onnxruntime


def onnx_name(model):
    """The name the ONNX files of `model` start with."""
    return f"nonlinear_ae_k{model.k}_h{model.hidden}"


def onnx_file_path(folder, model, precision):
    """The ONNX file of `model` in `folder`, `precision` being `float` or `int8`."""
    return os.path.join(folder, f"{onnx_name(model)}_{precision}.onnx")


def onnx_residuals(path, rows, batch=8192):
    """Each row's mean squared reconstruction error from the ONNX file at `path`."""
    session = onnxruntime.InferenceSession(path, providers=["CPUExecutionProvider"])
    out = []
    for fed in np.array_split(np.asarray(rows, dtype=np.float32),
                              max(len(rows) // batch, 1)):
        got = session.run(None, {"row": fed})[0]
        out.append(((got - fed) ** 2).mean(axis=1))
    return np.concatenate(out)


def onnx_scorer(folder, precision):
    """What scores rows with a model in ONNX Runtime, on its `precision` file."""
    return lambda model: partial(onnx_residuals,
                                 onnx_file_path(folder, model, precision))
