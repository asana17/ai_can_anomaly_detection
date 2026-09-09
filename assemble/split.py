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


def hold_out(logs: Iterable[str], frac: float, weight=None, blocks: int = 1,
             gap: int = 0):
    """Take `blocks` stretches out of the logs, and return what is left and them.

    Each stretch is contiguous and sits in the middle of its share of the sequence, so
    the calibration set covers the whole period without any of it being shuffled.
    `gap` logs on each side are dropped from both parts, because a log next to a
    calibration one resembles it too closely to calibrate against.
    """
    ordered, sizes = _ordered(logs, weight)
    upto = [0.0] + list(accumulate(sizes))
    want = upto[-1] * frac / blocks
    held, dropped = set(), set()
    for i in range(blocks):
        middle = upto[-1] * (i + 0.5) / blocks
        start = _cut(sizes, max(middle - want / 2, 0.0))
        stop = max(_cut(sizes, upto[start] + want), start + 1)
        held.update(range(start, min(stop, len(ordered))))
        dropped.update(range(max(start - gap, 0), start))
        dropped.update(range(stop, min(stop + gap, len(ordered))))
    dropped -= held
    return ([p for i, p in enumerate(ordered) if i not in held and i not in dropped],
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
