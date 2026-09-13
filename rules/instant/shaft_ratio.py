"""Flag the transmission output shaft turning at the wrong rate for the wheel speed.

The two are tied by the final drive and the tyre size, both fixed, so their ratio
holds whatever the gear or the engine is doing.
"""

from __future__ import annotations

# Measured over 178,460 evaluations above the gate, where the ratio runs 14.8 to
# 15.6 at motorway speed and widens as the wheel slows. See rules/measurements.md.
BOUNDS = (13.0, 17.5)


def violations(values: dict, min_speed: float, bounds: tuple = BOUNDS) -> list:
    """The pair of names, if the shaft and the wheel disagree on how fast the truck goes.

    Below `min_speed` the wheel speed is small enough that its quantisation dominates
    the ratio, which widens to 10 to 24 below 5 km/h and carries no signal.
    """
    shaft, wheel = values.get("output_shaft_speed"), values.get("wheel_speed")
    if shaft is None or wheel is None or wheel < min_speed:
        return []
    if bounds[0] <= shaft / wheel <= bounds[1]:
        return []
    return ["output_shaft_speed", "wheel_speed"]
