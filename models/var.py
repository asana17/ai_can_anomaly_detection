"""Score a window by how far its last row sits from what the rows before it predict.

A vector autoregression fit on normal windows predicts the last row as a linear
function of every row before it in the window. An attack that breaks how the signals
follow each other in time shows up as a large error on that row.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
from sklearn.linear_model import LinearRegression


class Autoregression(NamedTuple):
    coefficients: np.ndarray    # (signals, rows before the last * signals), coef_
    intercept: np.ndarray       # (signals,), intercept_


def _before_last(windows: np.ndarray) -> np.ndarray:
    """The rows before the last of each window, oldest first, as one row per window."""
    return windows[:, :-1].reshape(len(windows), -1)


def autoregression(windows: np.ndarray) -> Autoregression:
    """The least squares fit of each window's last row on the rows before it.

    `windows` is (windows, rows, signals), each window oldest first.
    """
    fitted = LinearRegression().fit(_before_last(windows), windows[:, -1])
    return Autoregression(fitted.coef_, fitted.intercept_)


def residuals(windows: np.ndarray, fitted: Autoregression) -> np.ndarray:
    """Each window's mean squared error on its last row."""
    predicted = _before_last(windows) @ fitted.coefficients.T + fitted.intercept
    return ((windows[:, -1] - predicted) ** 2).mean(axis=1)
