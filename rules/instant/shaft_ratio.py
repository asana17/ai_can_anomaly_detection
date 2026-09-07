"""Flag the transmission output shaft turning at the wrong rate for the wheel speed.

The two are tied by the final drive and the tyre size, both fixed, so their ratio
holds whatever the gear or the engine is doing.
"""

from __future__ import annotations

# Measured over 178,460 evaluations above the gate, where the ratio runs 14.8 to
# 15.6 at motorway speed and widens as the wheel slows. See rules/measurements.md.
BOUNDS = (13.0, 17.5)

# Below this the wheel speed is small enough that its quantisation dominates the
# ratio, which widens to 10 to 24 and carries no signal.
MIN_SPEED = 5.0


def violations(values: dict, bounds: tuple = BOUNDS, min_speed: float = MIN_SPEED) -> list:
    """The pair of names, if the shaft and the wheel disagree on how fast the truck goes."""
    shaft, wheel = values.get("output_shaft_speed"), values.get("wheel_speed")
    if shaft is None or wheel is None or wheel < min_speed:
        return []
    if bounds[0] <= shaft / wheel <= bounds[1]:
        return []
    return ["output_shaft_speed", "wheel_speed"]
