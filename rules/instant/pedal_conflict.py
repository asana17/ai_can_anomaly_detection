"""Flag the accelerator and the brake being pressed at once.

Never seen together in 486,544 evaluations. See rules/measurements.md.
"""

from __future__ import annotations

# A pedal resting on its stop reports a little above zero, so neither counts as
# pressed until it clears this.
PRESSED = 1.0

NAMES = ["accel_pedal", "brake_pedal"]


def violations(values: dict, pressed: float = PRESSED) -> list:
    """The two names, if both pedals report pressed."""
    accel, brake = values.get("accel_pedal"), values.get("brake_pedal")
    if accel is None or brake is None:
        return []
    return NAMES if accel > pressed and brake > pressed else []
