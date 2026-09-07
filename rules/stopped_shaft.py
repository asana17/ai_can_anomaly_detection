"""Flag the transmission output shaft turning while the wheels report stopped.

shaft_ratio checks the same two but needs the truck moving, so nothing checks them
while the truck is stopped. This covers that.
"""

from __future__ import annotations

# The shaft reads up to 31 rpm with the wheels at zero, over 278,819 evaluations.
# See docs/measurements.md.
MAX_SHAFT = 50.0

NAMES = ["wheel_speed", "output_shaft_speed"]


def violations(values: dict, max_shaft: float = MAX_SHAFT) -> list:
    """The two names, if the wheels read stopped and the shaft does not."""
    wheel, shaft = values.get("wheel_speed"), values.get("output_shaft_speed")
    if wheel is None or shaft is None or wheel != 0:
        return []
    return NAMES if shaft > max_shaft else []
