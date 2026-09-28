"""What a model's ONNX files are named, where they are fetched from, and how rows are
scored with one."""

from __future__ import annotations

import os
from functools import partial

import numpy as np
import onnxruntime

from common.hub_dirs import read_dir


def onnx_file_path(folder, model, precision):
    """The ONNX file of `model` in `folder`, `precision` being `float` or `int8`."""
    return os.path.join(folder, f"{model.onnx_name}_{precision}.onnx")


def fetch_onnx_files(runs_repo, revision, onnx_path, models_path, runs_dir):
    """The folder the ONNX files of `onnx_path`, at `revision` of `runs_repo`, are
    downloaded into, and its `meta.json`. Raises unless they are made from
    `models_path`."""
    folder, meta = read_dir(runs_repo, onnx_path, runs_dir, revision)
    made_from = meta["models"]["path"]
    if made_from != models_path:
        raise ValueError(f"{onnx_path} is made from {made_from}, not {models_path}")
    return folder, meta


def onnx_residuals(path, rows, batch=8192, signals=None):
    """Each input's mean squared reconstruction error from the ONNX file at `path`, over
    its last `signals` values, or over all of them when `signals` is None.

    An input is one row, or a window of rows laid out oldest first, where the last
    `signals` values are its last row.
    """
    session = onnxruntime.InferenceSession(path, providers=["CPUExecutionProvider"])
    out = []
    for fed in np.array_split(np.asarray(rows, dtype=np.float32),
                              max(len(rows) // batch, 1)):
        errors = (session.run(None, {"row": fed})[0] - fed) ** 2
        if signals is not None:
            errors = errors[:, -signals:]
        out.append(errors.mean(axis=1))
    return np.concatenate(out)


def onnx_scorer(folder, precision):
    """What scores rows with a model in ONNX Runtime, on its `precision` file."""
    return lambda model: partial(onnx_residuals,
                                 onnx_file_path(folder, model, precision))


def onnx_window_scorer(folder, precision):
    """What scores windows with a window model in ONNX Runtime, on its `precision` file.
    A window of shape (rows, signals) goes in as one row, and scores by the error on its
    last row, as in torch."""
    def scorer_of(model):
        path = onnx_file_path(folder, model, precision)
        return lambda windows: onnx_residuals(path, model.flat(windows),
                                              signals=windows.shape[2])
    return scorer_of
