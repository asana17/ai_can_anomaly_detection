"""Mark the rows whose wheel speed is above a given speed."""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS


def moving(raw: np.ndarray, *, min_speed: float) -> np.ndarray:
    """True where a row's wheel speed is above `min_speed`, read off physical values."""
    return raw[:, SIGNALS.index("wheel_speed")] > min_speed
