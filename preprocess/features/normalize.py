"""Standardize signal vectors with z-scores fit on training data."""

from __future__ import annotations

from math import sqrt
from typing import Iterable


def fit(vectors: Iterable[list]) -> list[tuple[float, float]]:
    """Return each signal's (mean, std) over the vectors."""
    count = mean = m2 = None
    for v in vectors:
        if count is None:
            count = [0] * len(v)
            mean = [0.0] * len(v)
            m2 = [0.0] * len(v)
        for i, x in enumerate(v):
            count[i] += 1
            delta = x - mean[i]
            mean[i] += delta / count[i]
            m2[i] += delta * (x - mean[i])
    return [
        (mean[i], sqrt(m2[i] / count[i]) if count[i] else 0.0)
        for i in range(len(mean))
    ]


def normalize(vector: list, stats: list[tuple[float, float]]) -> list:
    """Z-score a vector with the given (mean, std) stats."""
    return [(x - mean) / std if std else 0.0 for x, (mean, std) in zip(vector, stats)]
