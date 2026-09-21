"""The units rows are expressed in, fitted once and handed to everything else."""

from __future__ import annotations

import numpy as np

from preprocess.features.scale import Scale


def scale_for(rows: np.ndarray) -> Scale:
    """The mean and std to z-score on, taken from the rows a model is fitted on."""
    std = rows.std(axis=0)
    std[std == 0] = 1.0                       # a constant signal stays at 0
    return Scale(rows.mean(axis=0), std)
