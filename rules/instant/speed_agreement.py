"""Flag the two vehicle speeds disagreeing.

CCVS1 and TCO1 each report the vehicle's speed, from different senders. An attack
that rewrites one PGN does not move the other, so a disagreement is visible even
though both readings stay inside their own range.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# Normally the two sit within 0.9 km/h of each other at p99, and more than 2 km/h
# apart on 0.006% of rows. See rules/measurements.md.
MAX_DISAGREEMENT = 2.0


def hits(raw: np.ndarray, limit: float = MAX_DISAGREEMENT) -> np.ndarray:
    """True where the two speeds disagree by more than `limit`."""
    wheel = raw[:, SIGNALS.index("wheel_speed")]
    tacho = raw[:, SIGNALS.index("tachograph_speed")]
    return np.abs(wheel - tacho) > limit
