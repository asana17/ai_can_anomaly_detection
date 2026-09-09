"""Put logs on the grid and z-score them into the rows a model reads."""

from __future__ import annotations

import os
from typing import NamedTuple

import numpy as np

from assemble.grid import MAX_HOLD, PERIOD, starts_segment, to_arrays
from preprocess.features.grid_sample import resample
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


def grid_rows(logs) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Put every log on the grid, returning the rows, their times, and segment ids."""
    rows, times, segments = [], [], []
    segment = -1
    for path in logs:
        previous = None
        for t, row in resample(load_can_log(path), PERIOD, MAX_HOLD):
            if starts_segment(previous, t):
                segment += 1                # a new log, or the grid restarted
            rows.append(row)
            times.append(t)
            segments.append(segment)
            previous = t
    return to_arrays(rows, times, segments)


def scaled_rows(logs) -> dict:
    """Put `logs` on the grid and z-score them on their own mean and std."""
    rows, times, segments = grid_rows(logs)
    std = rows.std(axis=0)
    std[std == 0] = 1.0                       # a constant signal stays at 0
    scale = Scale(rows.mean(axis=0), std)
    return {"scale": scale, "rows": scale.apply(rows), "raw": rows,
            "t": times, "seg": segments}


def save(data: dict, out_dir: str) -> None:
    """Write each array in `data` to `out_dir` as a .npy file."""
    os.makedirs(out_dir, exist_ok=True)
    for name, value in data.items():
        if isinstance(value, Scale):
            value.save(out_dir)               # as mean.npy and std.npy
        else:
            np.save(os.path.join(out_dir, f"{name}.npy"), value)
