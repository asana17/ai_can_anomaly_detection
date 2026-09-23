"""Flag the steering angle and the yaw rate turning opposite ways.

Steering left turns the truck left. The two need not agree on how much, only on
which way, which holds where a magnitude check does not.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# Below this the truck is going straight and the sign of either signal is noise.
# At 0.02 the rule fired on 2,545 of the 2,757,787 moving grid rows of every log, at
# 0.05 on 191. See rules/measurements.md.
MIN_YAW = 0.05

def hits(raw: np.ndarray, min_speed: float, min_yaw: float = MIN_YAW) -> np.ndarray:
    """True where the wheel is turned one way and the truck is turning the other.

    Below `min_speed` the wheel can be turned without the truck changing direction.
    """
    steering = raw[:, SIGNALS.index("steering_angle")]
    yaw = raw[:, SIGNALS.index("yaw_rate")]
    speed = raw[:, SIGNALS.index("wheel_speed")]
    return ((speed >= min_speed) & (np.abs(yaw) >= min_yaw)
            & ((steering > 0) != (yaw > 0)))
