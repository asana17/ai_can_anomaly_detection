"""Flag the engine reading stopped while something it drives is still running.

A stopped engine burns no fuel, makes no torque, and turns no input shaft. This holds
where the ratio rules do not, since they all need the truck to be moving.
"""

from __future__ import annotations

# Every one of these read exactly zero on all 97,237 stopped evaluations measured.
# See docs/measurements.md.
MUST_BE_ZERO = ["fuel_rate", "actual_engine_torque", "engine_load",
                "driver_demand_torque", "accel_pedal", "input_shaft_speed"]


def violations(values: dict) -> list:
    """The engine speed and whatever is still moving with it, if any is."""
    engine = values.get("engine_speed")
    if engine is None or engine != 0:
        return []
    moving = [n for n in MUST_BE_ZERO if values.get(n)]
    return ["engine_speed"] + moving if moving else []
