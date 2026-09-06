"""Flag the two vehicle speeds disagreeing.

CCVS1 and TCO1 each report the vehicle's speed, from different senders. An attack
that rewrites one message does not move the other, so a disagreement is visible even
though both readings stay inside their own range.
"""

from __future__ import annotations

# Normally the two sit within 0.9 km/h of each other at p99, and more than 2 km/h
# apart on 0.006% of rows. See docs/measurements.md.
MAX_DISAGREEMENT = 2.0


def violations(values: dict, limit: float = MAX_DISAGREEMENT) -> list:
    """The pair of speed names, if both are present and disagree by more than `limit`."""
    wheel, tacho = values.get("wheel_speed"), values.get("tachograph_speed")
    if wheel is None or tacho is None or abs(wheel - tacho) <= limit:
        return []
    return ["wheel_speed", "tachograph_speed"]
