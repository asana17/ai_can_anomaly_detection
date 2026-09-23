"""Flag the engine reading stopped while something it drives is still running.

A stopped engine burns no fuel, makes no torque, and turns no input shaft. This holds
where the ratio rules do not, since they all need the truck to be moving.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# Over every log the rule fires on 141,110 of 36,041,922 evaluations with the engine
# at zero, 139,318 of them the input shaft still turning at 100 to 312 rpm. None of
# them is a moving grid row. See rules/measurements.md.
MUST_BE_ZERO = ["fuel_rate", "actual_engine_torque", "engine_load",
                "driver_demand_torque", "accel_pedal", "input_shaft_speed"]


def hits(raw: np.ndarray) -> np.ndarray:
    """True where the engine reads stopped and something it drives does not.

    A NaN, a value J1939 reserves, compares false both ways and so never fires.
    """
    engine = raw[:, SIGNALS.index("engine_speed")]
    driven = raw[:, [SIGNALS.index(name) for name in MUST_BE_ZERO]]
    return (engine == 0) & ((driven < 0) | (driven > 0)).any(axis=1)
