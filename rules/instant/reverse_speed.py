"""Flag the truck reporting reverse while moving faster than it can back up.

Reversing is slow. Nothing else ties the reported gear to the speed once the gear is
negative, since the ratio rules only hold for forward gears.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# Reverse never exceeded 3.5 km/h over 87,245 evaluations. See rules/measurements.md.
MAX_SPEED = 10.0

def hits(raw: np.ndarray, max_speed: float = MAX_SPEED) -> np.ndarray:
    """True where reverse is engaged above a speed reverse cannot reach."""
    gear = raw[:, SIGNALS.index("current_gear")]
    wheel = raw[:, SIGNALS.index("wheel_speed")]
    return (gear < 0) & (wheel > max_speed)
