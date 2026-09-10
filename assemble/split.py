"""Split the logs by time, without shuffling, and take a calibration set out."""

from __future__ import annotations

import os
from itertools import accumulate
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


def hold_out(logs: Iterable[str], count: int, weight=None):
    """Take `count` logs out of the ordered logs, and return what is left and them.

    They are spread evenly over the weight the logs carry, which `driving_time` sets
    to the seconds above `MIN_SPEED`, so what is taken covers the period the logs
    given cover without any of it being shuffled.
    """
    ordered, sizes = _ordered(logs, weight)
    total = sum(sizes)
    held: set[int] = set()
    for i in range(min(count, len(ordered))):
        at = min(_cut(sizes, total * (i + 0.5) / count), len(ordered) - 1)
        while at in held:                  # one log can hold two of the stretches
            at += 1
        if at == len(ordered):
            at = max(j for j in range(len(ordered)) if j not in held)
        held.add(at)
    return ([p for i, p in enumerate(ordered) if i not in held],
            [p for i, p in enumerate(ordered) if i in held])


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
