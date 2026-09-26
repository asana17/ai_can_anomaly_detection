"""Flag a signal moving further in one tick than the truck can move it.

Unlike the rules in instant, this one compares a grid row with the row before it.
See rules/sequence/docs/change_limit.md.
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


def hits(raw: np.ndarray, position: np.ndarray, limits: dict = LIMITS) -> np.ndarray:
    """True where a signal of a row moved further from the row before than a tick allows.

    `position` is each row's index, from 0, in its unbroken span of moving rows, and -1
    off them. A row at 0 or -1 has no row before and never fires. A NaN compares false
    and never fires.
    """
    # A grid row holds float32.
    columns = [SIGNALS.index(name) for name in limits]
    limit = np.array(list(limits.values()), dtype=np.float32)
    values = raw[:, columns].astype(np.float32)
    after = np.flatnonzero(np.asarray(position) >= 1)
    step = np.abs(values[after] - values[after - 1])
    flagged = np.zeros(len(raw), dtype=bool)
    flagged[after] = (step / np.float32(PERIOD) > limit).any(axis=1)
    return flagged
