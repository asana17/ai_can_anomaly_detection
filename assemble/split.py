"""Split log files by time, without shuffling, and hold blocks out for calibration."""

from __future__ import annotations

import os
from itertools import accumulate
from typing import Iterable

from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import load_can_log
from preprocess.frames.frame_decode import decode_frame

CCVS1 = 65265
DEFAULT_GATE = 5.0          # km/h, the speed the model's scoring is gated at


def moving_frames(files: Iterable[str], gate: float = DEFAULT_GATE) -> dict[str, int]:
    """Count each log's wheel speed readings above `gate`, as a weight for the splits."""
    counts = {}
    for path in files:
        seen = 0
        for f in load_can_log(path):
            if decompose_can_id(f.can_id).pgn == CCVS1:
                speed = decode_frame(CCVS1, f.data).get("wheel_speed")
                if speed is not None and speed > gate:
                    seen += 1
        counts[path] = seen
    return counts


def split(files: Iterable[str], train_frac: float, weight=None):
    """Cut the ordered files in two, everything after `train_frac` being the test set.

    `weight` says how much each file counts for, so the fraction becomes a share of
    that rather than of the file count.
    """
    ordered, sizes = _ordered(files, weight)
    cut = _cut(sizes, sum(sizes) * train_frac)
    return ordered[:cut], ordered[cut:]


def hold_out(files: Iterable[str], frac: float, weight=None, blocks: int = 1,
             gap: int = 0):
    """Take `blocks` stretches out of the files for calibration, and return both parts.

    Each stretch is contiguous and sits in the middle of its share of the sequence, so
    the held out set covers the whole period without any of it being shuffled. `gap`
    files on each side are dropped from both parts, because a file next to a held out
    one resembles it too closely to calibrate against.
    """
    ordered, sizes = _ordered(files, weight)
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


def _ordered(files, weight):
    """The files oldest first, with the weight of each."""
    ordered = sorted(files, key=os.path.basename)    # filename is a timestamp
    sizes = [1.0] * len(ordered) if weight is None else [weight[p] for p in ordered]
    return (ordered, sizes) if sum(sizes) else (ordered, [1.0] * len(ordered))


def _cut(sizes, target: float) -> int:
    """How many files fit inside `target`."""
    run, i = 0.0, 0
    while i < len(sizes) and run + sizes[i] <= target:
        run += sizes[i]
        i += 1
    return i
