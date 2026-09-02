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
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample every file on the grid, returning the rows, their times, and segment ids."""
    rows, times, segments = [], [], []
    segment = -1
    for path in files:
        previous = None
        for t, vec in resample(load_can_log(path), period, max_hold):
            if previous is None or t - previous > period * 1.5:
                segment += 1                # a new file, or the grid restarted
            rows.append(vec)
            times.append(t)
            segments.append(segment)
            previous = t
    return (
        np.asarray(rows, dtype=np.float32),
        np.asarray(times, dtype=np.float64),    # epoch seconds need the precision
        np.asarray(segments, dtype=np.int32),
    )


def build(
    train_files,
    val_files,
    test_files,
    period: float = DEFAULT_PERIOD,
    max_hold: float = DEFAULT_MAX_HOLD,
) -> dict:
    """Z-score each split on train's stats, and return the rows, times and segment ids."""
    train, train_t, train_seg = vectorize(train_files, period, max_hold)
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std[std == 0] = 1.0                       # a constant signal stays at 0

    data = {"mean": mean, "std": std}
    data.update(train=(train - mean) / std, train_t=train_t, train_seg=train_seg)
    for name, files in (("val", val_files), ("test", test_files)):
        rows, times, segments = vectorize(files, period, max_hold)
        data[name] = (rows - mean) / std if rows.size else rows
        data[f"{name}_t"] = times
        data[f"{name}_seg"] = segments
    return data


def save(data: dict, out_dir: str) -> None:
    """Write each array in `data` to `out_dir` as a .npy file."""
    os.makedirs(out_dir, exist_ok=True)
    for name, array in data.items():
        np.save(os.path.join(out_dir, f"{name}.npy"), array)
