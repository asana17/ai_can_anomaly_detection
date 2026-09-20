"""Put logs on the grid and take the scale a model's rows are z-scored on."""

from __future__ import annotations

import numpy as np

from assemble.grid import MAX_HOLD, PERIOD, moving, starts_segment, to_arrays
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


def split_rows(raw, times, share: float, block: float, gap: float, min_speed: float):
    """Split the training rows into train and calibration, as two masks over them.

    The rows that set a threshold must be ones the model never saw. Calibration takes
    `share` of the seconds above `min_speed`, in windows of `block` seconds. Train is
    the rest, less the rows within `gap` seconds of a window, which are in neither.
    """
    above = moving(raw, min_speed)
    seconds = (np.cumsum(above) - above) * PERIOD   # above min_speed, before this row
    calibration_rows = above & (seconds % (block / share) < block)
    apart = _apart(times, np.sort(times[calibration_rows]), gap)
    return ~calibration_rows & apart, calibration_rows


def apart_from_test(times, start: float, end: float, gap: float):
    """Which rows sit more than `gap` seconds outside the test block, `start` to `end`.

    The rows within `gap` of it go to neither train nor calibration.
    """
    return (times < start - gap) | (times > end + gap)


def _apart(times, windows, gap: float):
    """Which rows sit more than `gap` seconds from every row in `windows`.

    A brake or a gear change can run across the edge of a window, so the rows either
    side of one go to neither set.
    """
    if not len(windows):
        return np.ones(len(times), bool)
    near = np.searchsorted(windows, times)
    before = windows[np.clip(near - 1, 0, len(windows) - 1)]
    after = windows[np.clip(near, 0, len(windows) - 1)]
    return np.minimum(np.abs(times - before), np.abs(times - after)) > gap


def scale_for(rows: np.ndarray) -> Scale:
    """The mean and std to z-score on, taken from the rows a model is fitted on."""
    std = rows.std(axis=0)
    std[std == 0] = 1.0                       # a constant signal stays at 0
    return Scale(rows.mean(axis=0), std)
