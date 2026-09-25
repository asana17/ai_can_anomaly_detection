"""Flag a signal moving further in one tick than the truck can move it.

Unlike the rules in instant, this one compares a grid row with the row before it, so
the caller has to find that row. See rules/sequence/docs/change_limit.md.
"""

from __future__ import annotations

import numpy as np

from common.settings import GridSettings
from preprocess.features.signal_state import SIGNALS

PERIOD = GridSettings.PERIOD    # seconds from the row before, one tick

# Per second, from the steps between two moving grid rows. See rules/measurements.md.
LIMITS = {
    "actual_engine_torque": 400.0,  # %/s
    "brake_pedal": 250.0,       # %/s
    "engine_speed": 2600.0,     # rpm/s
    "steering_angle": 10.0,     # rad/s
    "tachograph_speed": 40.0,   # km/h/s
    "wheel_speed": 40.0,        # km/h/s
    "yaw_rate": 0.4,            # rad/s2
}


def hits(raw: np.ndarray, previous: np.ndarray, limits: dict = LIMITS) -> np.ndarray:
    """True where a signal of a row moved further from `previous` than a tick allows.

    `previous` holds the row before each row of `raw`, all NaN where there is none.
    A NaN compares false and never fires.
    """
    # A grid row holds float32, and the board computes in float32 too.
    columns = [SIGNALS.index(name) for name in limits]
    limit = np.array(list(limits.values()), dtype=np.float32)
    step = np.abs(raw[:, columns].astype(np.float32)
                  - previous[:, columns].astype(np.float32))
    return (step / np.float32(PERIOD) > limit).any(axis=1)
