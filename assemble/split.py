"""Split the logs by time, without shuffling, and take a calibration set out."""

from __future__ import annotations

import os
from typing import Iterable

import numpy as np

from assemble.grid import PERIOD
from preprocess.features.signal_state import SIGNALS
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import load_can_log
from preprocess.frames.frame_decode import decode_frame

CCVS1 = 65265
CCVS1_PERIOD = 0.1      # seconds between wheel speed readings
MIN_SPEED = 5.0         # km/h, the speed below which nothing here is scored
WHEEL = SIGNALS.index("wheel_speed")


def driving_time(logs: Iterable[str], min_speed: float = MIN_SPEED) -> dict[str, float]:
    """How many seconds each log spends above `min_speed`, as a weight for the splits.

    Every log is read, which takes about as long as building the arrays from them.
    """
    seconds = {}
    for path in logs:
        readings = 0
        for f in load_can_log(path):
            if decompose_can_id(f.can_id).pgn == CCVS1:
                speed = decode_frame(CCVS1, f.data).get("wheel_speed")
                if speed is not None and speed > min_speed:
                    readings += 1
        seconds[path] = readings * CCVS1_PERIOD
    return seconds


def split(seconds: dict[str, float], train_frac: float):
    """Cut the logs in two by time, everything after `train_frac` being the test set.

    `seconds` is what `driving_time` returns, so the fraction is a share of the seconds
    above the minimum speed rather than of the log count.
    """
    ordered = sorted(seconds, key=os.path.basename)     # filename is a timestamp
    sizes = [seconds[p] for p in ordered]
    cut = _cut(sizes, sum(sizes) * train_frac)
    return ordered[:cut], ordered[cut:]


def split_rows(raw, times, share: float, block: float, gap: float,
               min_speed: float = MIN_SPEED):
    """Split the training rows into train and calibration, as two masks over them.

    The rows that set a threshold must be ones the model never saw. Calibration takes
    `share` of the seconds above `min_speed`, in windows of `block` seconds. Train is
    the rest, less the rows within `gap` seconds of a window, which are in neither.
    """
    moving = raw[:, WHEEL] > min_speed
    seconds = (np.cumsum(moving) - moving) * PERIOD   # above min_speed, before this row
    calibration_rows = moving & (seconds % (block / share) < block)
    apart = _apart(times, np.sort(times[calibration_rows]), gap)
    return ~calibration_rows & apart, calibration_rows


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


def _cut(sizes, target: float) -> int:
    """How many logs fit inside `target`."""
    run, i = 0.0, 0
    while i < len(sizes) and run + sizes[i] <= target:
        run += sizes[i]
        i += 1
    return i
