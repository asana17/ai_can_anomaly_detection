"""Build the normalized train/val/test arrays that the model trains on."""

from __future__ import annotations

import os

import numpy as np

from preprocess.features.grid_sample import resample
from preprocess.frames.can_log_loader import load_can_log


def vectorize(files, period: float) -> np.ndarray:
    """Sample every file on the grid and stack the rows into one array (grid resets per file)."""
    rows = [vec for f in files for _, vec in resample(load_can_log(f), period)]
    return np.asarray(rows, dtype=np.float32)


def build(train_files, val_files, test_files, period: float) -> dict:
    """Z-score each split, fitting mean and std on train only, and return arrays plus stats."""
    train = vectorize(train_files, period)
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std[std == 0] = 1.0                       # a constant signal stays at 0

    def apply(files) -> np.ndarray:
        a = vectorize(files, period)
        return (a - mean) / std if a.size else a

    return {
        "mean": mean,
        "std": std,
        "train": (train - mean) / std,
        "val": apply(val_files),
        "test": apply(test_files),
    }


def save(data: dict, out_dir: str) -> None:
    """Write each array in `data` to `out_dir` as a .npy file."""
    os.makedirs(out_dir, exist_ok=True)
    for name in ("train", "val", "test", "mean", "std"):
        np.save(os.path.join(out_dir, f"{name}.npy"), data[name])
