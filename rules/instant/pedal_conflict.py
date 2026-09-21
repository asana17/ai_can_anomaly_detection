"""Flag the accelerator and the brake being pressed at once.

Never seen together in 486,544 evaluations. See rules/measurements.md.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# A pedal resting on its stop reports a little above zero, so neither counts as
# pressed until it clears this.
PRESSED = 1.0

def hits(raw: np.ndarray, pressed: float = PRESSED) -> np.ndarray:
    """True where both pedals report pressed."""
    accel = raw[:, SIGNALS.index("accel_pedal")]
    brake = raw[:, SIGNALS.index("brake_pedal")]
    return (accel > pressed) & (brake > pressed)
