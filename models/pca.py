"""Score a row by how far it sits off the subspace normal traffic occupies.

Principal components fit on normal rows span the directions those rows vary in.
Anything left over after projecting onto them is the residual, and an attack that
moves a row off that subspace shows up in it.
"""

from __future__ import annotations

import numpy as np


def fit(rows: np.ndarray, components: int) -> np.ndarray:
    """The `components` directions normal rows vary in most, as a (signals, k) basis."""
    centred = rows - rows.mean(axis=0)
    _, _, vt = np.linalg.svd(centred, full_matrices=False)
    return vt[:components].T


def residuals(rows: np.ndarray, basis: np.ndarray) -> np.ndarray:
    """How far each row sits off the subspace, one number per row."""
    projected = (rows @ basis) @ basis.T
    return np.linalg.norm(rows - projected, axis=1)


def explained(rows: np.ndarray) -> np.ndarray:
    """The share of variance each component accounts for, largest first."""
    centred = rows - rows.mean(axis=0)
    s = np.linalg.svd(centred, compute_uv=False)
    return s ** 2 / (s ** 2).sum()
