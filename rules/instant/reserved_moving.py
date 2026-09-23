"""Flag a reserved value, not available or an error, while the truck moves.

The other rules read a NaN as nothing to judge. That leaves a frame forged to carry
0xFF or 0xFE unseen, and the model does not score a row holding one either. The
truck only sends a reserved value with both speeds at 0, so on the move it is the
finding.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS


def hits(raw: np.ndarray) -> np.ndarray:
    """True where a signal is NaN and either vehicle speed is above 0.

    Either speed will do, so a reserved value put in one of them is still caught by
    the other.
    """
    wheel = raw[:, SIGNALS.index("wheel_speed")]
    tachograph = raw[:, SIGNALS.index("tachograph_speed")]
    moving = (wheel > 0) | (tachograph > 0)
    return moving & np.isnan(raw).any(axis=1)
