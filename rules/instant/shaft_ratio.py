"""Flag the transmission output shaft turning at the wrong rate for the wheel speed.

The two are tied by the final drive and the tyre size, both fixed, so their ratio
holds whatever the gear or the engine is doing.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# Measured over 178,460 evaluations above the gate, where the ratio runs 14.8 to
# 15.6 at motorway speed and widens as the wheel slows. See rules/measurements.md.
BOUNDS = (13.0, 17.5)


def hits(raw: np.ndarray, min_speed: float, bounds: tuple = BOUNDS) -> np.ndarray:
    """True where the shaft and the wheel disagree on how fast the truck goes.

    Below `min_speed` the wheel speed is small enough that its quantisation dominates
    the ratio, which widens to 10 to 24 below 5 km/h and carries no signal.
    """
    shaft = raw[:, SIGNALS.index("output_shaft_speed")]
    wheel = raw[:, SIGNALS.index("wheel_speed")]
    fast = wheel >= min_speed
    ratio = np.divide(shaft, wheel, out=np.zeros_like(wheel), where=fast)
    return fast & ((ratio < bounds[0]) | (ratio > bounds[1]))
