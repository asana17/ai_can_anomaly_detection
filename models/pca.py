"""Score a row by how far it sits off the subspace normal traffic occupies.

Principal components fit on normal rows span the directions those rows vary in.
Anything left over after projecting onto them is the residual, and an attack that
moves a row off that subspace shows up in it.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
from sklearn.decomposition import PCA


class Subspace(NamedTuple):
    centre: np.ndarray      # the mean the components were taken about, mean_
    basis: np.ndarray       # (signals, k), the directions themselves, components_.T


def subspace(rows: np.ndarray, components: int) -> Subspace:
    """The `components` directions normal rows vary in most, about their mean."""
    fitted = PCA(n_components=components, svd_solver="full").fit(rows)
    return Subspace(fitted.mean_, fitted.components_.T)


def residuals(rows: np.ndarray, space: Subspace) -> np.ndarray:
    """How far each row sits off the subspace, one number per row."""
    centred = rows - space.centre
    projected = (centred @ space.basis) @ space.basis.T
    return np.linalg.norm(centred - projected, axis=1)
