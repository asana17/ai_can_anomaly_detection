"""Split log files into train, validation, and test by time, without shuffling."""

from __future__ import annotations

import os
from typing import Iterable

from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import load_can_log
from preprocess.frames.frame_decode import decode_frame

CCVS1 = 65265
DEFAULT_GATE = 5.0          # km/h, the speed the model's scoring is gated at


def moving_frames(files: Iterable[str], gate: float = DEFAULT_GATE) -> dict[str, int]:
    """Count each log's wheel speed readings above `gate`, as a weight for `split`."""
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


def split(files: Iterable[str], train_frac: float, val_frac: float, weight=None):
    """Cut the ordered files into three chronological blocks.

    `weight` says how much each file counts for, so the fractions become shares of
    that rather than shares of the file count. Without it every file counts as one,
    which sizes validation in files rather than in the rows a threshold comes from.
    """
    ordered = sorted(files, key=os.path.basename)   # filename is a timestamp
    sizes = [1.0] * len(ordered) if weight is None else [weight[p] for p in ordered]
    total = sum(sizes)
    if not total:
        sizes, total = [1.0] * len(ordered), float(len(ordered))
    a = _cut(sizes, total * train_frac)
    b = _cut(sizes, total * (train_frac + val_frac))
    return ordered[:a], ordered[a:b], ordered[b:]


def _cut(sizes, target: float) -> int:
    """How many files fit inside `target`."""
    run, i = 0.0, 0
    while i < len(sizes) and run + sizes[i] <= target:
        run += sizes[i]
        i += 1
    return i
