"""The units rows are expressed in, fitted once and handed to everything else."""

from __future__ import annotations

import os
from typing import NamedTuple

import numpy as np


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
