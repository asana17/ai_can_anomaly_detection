"""Build the normalized train/val/test arrays that the model trains on."""

from __future__ import annotations

import os

import numpy as np

from preprocess.features.grid_sample import DEFAULT_MAX_HOLD, DEFAULT_PERIOD, resample
from preprocess.frames.can_log_loader import load_can_log


def vectorize(
    files,
    period: float = DEFAULT_PERIOD,
    max_hold: float = DEFAULT_MAX_HOLD,
) -> np.ndarray:
    """Sample every file on the grid and stack the rows into one array (grid resets per file)."""
    rows = [vec for f in files for _, vec in resample(load_can_log(f), period, max_hold)]
    return np.asarray(rows, dtype=np.float32)


def build(
    train_files,
    val_files,
    test_files,
    period: float = DEFAULT_PERIOD,
    max_hold: float = DEFAULT_MAX_HOLD,
) -> dict:
    """Z-score each split, fitting mean and std on train only, and return arrays plus stats."""
    train = vectorize(train_files, period, max_hold)
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std[std == 0] = 1.0                       # a constant signal stays at 0

    def apply(files) -> np.ndarray:
        a = vectorize(files, period, max_hold)
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
