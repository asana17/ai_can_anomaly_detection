"""Put logs on the grid and take the scale a model's rows are z-scored on."""

from __future__ import annotations

import numpy as np

from assemble.grid import MAX_HOLD, PERIOD, starts_segment, to_arrays
from assemble.scale import Scale
from preprocess.features.grid_sample import resample
from preprocess.frames.can_log_loader import load_can_log


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


def scale_for(rows: np.ndarray) -> Scale:
    """The mean and std to z-score on, taken from the rows a model is fitted on."""
    std = rows.std(axis=0)
    std[std == 0] = 1.0                       # a constant signal stays at 0
    return Scale(rows.mean(axis=0), std)
