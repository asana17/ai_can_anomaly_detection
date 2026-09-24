"""Flag the engine reading stopped while something it drives is still running.

A stopped engine burns no fuel and makes no torque. This holds
where the ratio rules do not, since they all need the truck to be moving.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# The input shaft is left out. Over every log it still turns at 100 to 312 rpm on
# 139,318 of 36,041,922 evaluations with the engine at zero. Without it the rule fires
# on 1,836 of them. See rules/measurements.md.
MUST_BE_ZERO = ["fuel_rate", "actual_engine_torque", "engine_load",
                "driver_demand_torque", "accel_pedal"]


def hits(raw: np.ndarray) -> np.ndarray:
    """True where the engine reads stopped and something it drives does not.

    A NaN, a value J1939 reserves, compares false both ways and so never fires.
    """
    engine = raw[:, SIGNALS.index("engine_speed")]
    driven = raw[:, [SIGNALS.index(name) for name in MUST_BE_ZERO]]
    return (engine == 0) & ((driven < 0) | (driven > 0)).any(axis=1)
