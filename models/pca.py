"""Score a row by how far it sits off the subspace normal traffic occupies.

Principal components fit on normal rows span the directions those rows vary in.
Anything left over after projecting onto them is the residual, and an attack that
moves a row off that subspace shows up in it.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np


class Subspace(NamedTuple):
    centre: np.ndarray      # the mean the components were taken about
    basis: np.ndarray       # (signals, k), the directions themselves


def subspace(rows: np.ndarray, components: int) -> Subspace:
    """The `components` directions normal rows vary in most, about their mean."""
    centre = rows.mean(axis=0)
    _, _, vt = np.linalg.svd(rows - centre, full_matrices=False)
    return Subspace(centre, vt[:components].T)


def residuals(rows: np.ndarray, space: Subspace) -> np.ndarray:
    """How far each row sits off the subspace, one number per row."""
    centred = rows - space.centre
    projected = (centred @ space.basis) @ space.basis.T
    return np.linalg.norm(centred - projected, axis=1)


def variance_share(rows: np.ndarray) -> np.ndarray:
    """The share of variance each component accounts for, largest first."""
    s = np.linalg.svd(rows - rows.mean(axis=0), compute_uv=False)
    return s ** 2 / (s ** 2).sum()
