"""Flag a signal moving faster than the truck can move it.

Unlike the rules in instant, this one compares a reading with the one before it, so
the caller has to keep the previous value and the time since.
"""

from __future__ import annotations

# The most each signal moved per second over 25 logs, rounded up and doubled to
# leave room. Signals not listed are unbounded in practice, the input shaft because
# a shift lets it spin free and the gears because they jump. See docs/measurements.md.
LIMITS = {
    "yaw_rate": 3.0,            # rad/s2, observed 1.1
    "steering_angle": 40.0,     # rad/s, observed 16.4
    "wheel_speed": 50.0,        # km/h/s, observed 21.0
    "tachograph_speed": 100.0,  # km/h/s, observed 41.9
}


def violations(values: dict, previous: dict, seconds: float, limits: dict = LIMITS) -> list:
    """The names that moved further than `seconds` allows, in LIMITS order."""
    if seconds <= 0:
        return []
    out = []
    for name, limit in limits.items():
        now, before = values.get(name), previous.get(name)
        if now is not None and before is not None and abs(now - before) / seconds > limit:
            out.append(name)
    return out
