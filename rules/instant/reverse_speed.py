"""Flag the truck reporting reverse while moving faster than it can back up.

Reversing is slow. Nothing else ties the reported gear to the speed once the gear is
negative, since the ratio rules only hold for forward gears.
"""

from __future__ import annotations

# Reverse never exceeded 3.5 km/h over 87,245 evaluations. See docs/measurements.md.
MAX_SPEED = 10.0

NAMES = ["current_gear", "wheel_speed"]


def violations(values: dict, max_speed: float = MAX_SPEED) -> list:
    """The two names, if reverse is engaged above a speed reverse cannot reach."""
    gear, wheel = values.get("current_gear"), values.get("wheel_speed")
    if gear is None or wheel is None or gear >= 0:
        return []
    return NAMES if wheel > max_speed else []
