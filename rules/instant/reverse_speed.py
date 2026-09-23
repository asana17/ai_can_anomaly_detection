"""Flag the truck reporting reverse while moving faster than it can back up.

Reversing is slow. Nothing else ties the reported gear to the speed once the gear is
negative, since the ratio rules only hold for forward gears.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# Over every log reverse reads up to 38.3 km/h, in 9 runs where the gear stays at -1
# while the truck drives off. The limit fires on those, 9 of the 2,757,787 moving grid
# rows. See rules/measurements.md.
MAX_SPEED = 10.0

def hits(raw: np.ndarray, max_speed: float = MAX_SPEED) -> np.ndarray:
    """True where reverse is engaged above a speed reverse cannot reach."""
    gear = raw[:, SIGNALS.index("current_gear")]
    wheel = raw[:, SIGNALS.index("wheel_speed")]
    return (gear < 0) & (wheel > max_speed)
