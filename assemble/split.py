"""Split the logs into train and test by time, without shuffling."""

from __future__ import annotations

import os
from typing import Iterable

from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import load_can_log
from preprocess.frames.frame_decode import decode_frame

CCVS1 = 65265
CCVS1_PERIOD = 0.1      # seconds between wheel speed readings
MIN_SPEED = 5.0         # km/h, the speed below which nothing here is scored


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


def split(logs: Iterable[str], train_frac: float, weight=None):
    """Cut the ordered logs in two, everything after `train_frac` being the test set.

    `weight` says how much each log counts for, so the fraction becomes a share of
    that rather than of the log count.
    """
    ordered, sizes = _ordered(logs, weight)
    cut = _cut(sizes, sum(sizes) * train_frac)
    return ordered[:cut], ordered[cut:]


def _ordered(logs, weight):
    """The logs oldest first, with the weight of each."""
    ordered = sorted(logs, key=os.path.basename)     # filename is a timestamp
    sizes = [1.0] * len(ordered) if weight is None else [weight[p] for p in ordered]
    return (ordered, sizes) if sum(sizes) else (ordered, [1.0] * len(ordered))


def _cut(sizes, target: float) -> int:
    """How many logs fit inside `target`."""
    run, i = 0.0, 0
    while i < len(sizes) and run + sizes[i] <= target:
        run += sizes[i]
        i += 1
    return i
