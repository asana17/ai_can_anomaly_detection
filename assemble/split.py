"""Split log files into train, validation, and test by time, without shuffling."""

from __future__ import annotations

import os
from typing import Iterable


def split(files: Iterable[str], train_frac: float, val_frac: float):
    ordered = sorted(files, key=os.path.basename)   # filename is a timestamp
    n = len(ordered)
    a = int(n * train_frac)
    b = int(n * (train_frac + val_frac))
    return ordered[:a], ordered[a:b], ordered[b:]
