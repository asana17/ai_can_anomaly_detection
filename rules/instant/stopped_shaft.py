"""Flag the transmission output shaft turning while the wheels report stopped.

shaft_ratio checks the same two but needs the truck moving, so nothing checks them
while the truck is stopped. This covers that.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# Over every log the shaft reads up to 551 rpm with the wheels at zero, and above 50
# on 2,600 of 106,072,217 evaluations, where the tachograph speed shows the truck
# still rolling. None of them is a moving grid row. See rules/measurements.md.
MAX_SHAFT = 50.0

def hits(raw: np.ndarray, max_shaft: float = MAX_SHAFT) -> np.ndarray:
    """True where the wheels read stopped and the shaft does not."""
    wheel = raw[:, SIGNALS.index("wheel_speed")]
    shaft = raw[:, SIGNALS.index("output_shaft_speed")]
    return (wheel == 0) & (shaft > max_shaft)
