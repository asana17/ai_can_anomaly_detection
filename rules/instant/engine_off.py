"""Flag the engine reading stopped while something it drives is still running.

A stopped engine burns no fuel, makes no torque, and turns no input shaft. This holds
where the ratio rules do not, since they all need the truck to be moving.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# Every one of these read exactly zero on all 97,237 stopped evaluations measured.
# See rules/measurements.md.
MUST_BE_ZERO = ["fuel_rate", "actual_engine_torque", "engine_load",
                "driver_demand_torque", "accel_pedal", "input_shaft_speed"]


def hits(raw: np.ndarray) -> np.ndarray:
    """True where the engine reads stopped and something it drives does not."""
    engine = raw[:, SIGNALS.index("engine_speed")]
    driven = raw[:, [SIGNALS.index(name) for name in MUST_BE_ZERO]]
    return (engine == 0) & (driven != 0).any(axis=1)
