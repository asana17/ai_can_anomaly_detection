"""Flag the transmission output shaft turning while the wheels report stopped.

shaft_ratio checks the same two but needs the truck moving, so nothing checks them
while the truck is stopped. This covers that.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# The shaft reads up to 31 rpm with the wheels at zero, over 278,819 evaluations.
# See rules/measurements.md.
MAX_SHAFT = 50.0

def hits(raw: np.ndarray, max_shaft: float = MAX_SHAFT) -> np.ndarray:
    """True where the wheels read stopped and the shaft does not."""
    wheel = raw[:, SIGNALS.index("wheel_speed")]
    shaft = raw[:, SIGNALS.index("output_shaft_speed")]
    return (wheel == 0) & (shaft > max_shaft)
