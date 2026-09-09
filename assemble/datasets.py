"""Build the z-scored train, val and test arrays that the model reads."""

from __future__ import annotations

import os
from typing import NamedTuple

import numpy as np

from preprocess.features.grid_sample import DEFAULT_MAX_HOLD, DEFAULT_PERIOD, resample
from preprocess.frames.can_log_loader import load_can_log


class Scale(NamedTuple):
    """The z-score fitted on train, and the only way rows are put on that scale."""
    mean: np.ndarray
    std: np.ndarray

    def apply(self, rows: np.ndarray) -> np.ndarray:
        return (rows - self.mean) / self.std if rows.size else rows

    def undo(self, rows: np.ndarray) -> np.ndarray:
        return rows * self.std + self.mean

    def save(self, out_dir: str) -> None:
        np.save(os.path.join(out_dir, "mean.npy"), self.mean)
        np.save(os.path.join(out_dir, "std.npy"), self.std)


def grid_rows(
    logs,
    period: float = DEFAULT_PERIOD,
    max_hold: float = DEFAULT_MAX_HOLD,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Put every log on the grid, returning the rows, their times, and segment ids."""
    rows, times, segments = [], [], []
    segment = -1
    for path in logs:
        previous = None
        for t, row in resample(load_can_log(path), period, max_hold):
            if previous is None or t - previous > period * 1.5:
                segment += 1                # a new log, or the grid restarted
            rows.append(row)
            times.append(t)
            segments.append(segment)
            previous = t
    return (
        np.asarray(rows, dtype=np.float32),
        np.asarray(times, dtype=np.float64),    # epoch seconds need the precision
        np.asarray(segments, dtype=np.int32),
    )


def scaled_rows(
    train_logs,
    val_logs,
    test_logs,
    period: float = DEFAULT_PERIOD,
    max_hold: float = DEFAULT_MAX_HOLD,
) -> dict:
    """Z-score each split on train's stats, keeping the physical rows beside them."""
    train, train_t, train_seg = grid_rows(train_logs, period, max_hold)
    std = train.std(axis=0)
    std[std == 0] = 1.0                       # a constant signal stays at 0
    scale = Scale(train.mean(axis=0), std)

    data = {"scale": scale}
    for name, (rows, times, segments) in (
        ("train", (train, train_t, train_seg)),
        ("val", grid_rows(val_logs, period, max_hold)),
        ("test", grid_rows(test_logs, period, max_hold)),
    ):
        data[name] = scale.apply(rows)
        data[f"{name}_raw"] = rows
        data[f"{name}_t"] = times
        data[f"{name}_seg"] = segments
    return data


def save(data: dict, out_dir: str) -> None:
    """Write each array in `data` to `out_dir` as a .npy file."""
    os.makedirs(out_dir, exist_ok=True)
    for name, value in data.items():
        if isinstance(value, Scale):
            value.save(out_dir)               # as mean.npy and std.npy
        else:
            np.save(os.path.join(out_dir, f"{name}.npy"), value)
