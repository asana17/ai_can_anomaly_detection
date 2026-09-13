"""Flag the steering angle and the yaw rate turning opposite ways.

Steering left turns the truck left. The two need not agree on how much, only on
which way, which holds where a magnitude check does not.
"""

from __future__ import annotations

# Below this the truck is going straight and the sign of either signal is noise.
# Above it the two disagree on 0.0168% of evaluations. See rules/measurements.md.
MIN_YAW = 0.02

NAMES = ["steering_angle", "yaw_rate"]


def violations(values: dict, min_speed: float, min_yaw: float = MIN_YAW) -> list:
    """The two names, if the wheel is turned one way and the truck is turning the other.

    Below `min_speed` the wheel can be turned without the truck changing direction.
    """
    steering, yaw = values.get("steering_angle"), values.get("yaw_rate")
    speed = values.get("wheel_speed")
    if None in (steering, yaw, speed) or speed < min_speed or abs(yaw) < min_yaw:
        return []
    return NAMES if (steering > 0) != (yaw > 0) else []
