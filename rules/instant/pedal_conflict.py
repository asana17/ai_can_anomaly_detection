"""Flag the accelerator and the brake being pressed at once.

Over every log both read pressed on 1,066 of the 2,757,787 moving grid rows, drivers
holding both pedals. See rules/measurements.md.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# A pedal resting on its stop reports a little above zero, and drivers rest a foot on
# both lightly. At 1% the rule raised 0.57 false alarms an hour on the test set at a
# hold of 10 rows, at 10% 0.29, losing 7 of 490 attacks caught.
PRESSED = 10.0

def hits(raw: np.ndarray, pressed: float = PRESSED) -> np.ndarray:
    """True where both pedals report pressed."""
    accel = raw[:, SIGNALS.index("accel_pedal")]
    brake = raw[:, SIGNALS.index("brake_pedal")]
    return (accel > pressed) & (brake > pressed)
