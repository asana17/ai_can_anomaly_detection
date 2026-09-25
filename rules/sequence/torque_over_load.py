"""Flag actual_engine_torque above engine_load, averaged over the last rows.

See rules/sequence/docs/torque_over_load.md.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

ROWS = 10       # W, the rows averaged, up to and including the row judged
LIMIT = 3.5     # %, the most the mean of torque minus load may reach

TORQUE = SIGNALS.index("actual_engine_torque")
LOAD = SIGNALS.index("engine_load")


def hits(raw: np.ndarray, position: np.ndarray) -> np.ndarray:
    """True where torque minus load, averaged over `ROWS` rows, is above `LIMIT`.

    `position` holds the rows before each row in its run.
    """
    # A grid row holds float32, and the board computes in float32 too.
    step = (raw[:, TORQUE].astype(np.float32) - raw[:, LOAD].astype(np.float32))
    total = np.full(len(raw), np.nan, dtype=np.float32)
    ends = np.flatnonzero(np.asarray(position) >= ROWS - 1)
    if len(ends):
        # Oldest first, one add at a time, the order the board adds in.
        total[ends] = step[ends - (ROWS - 1)]
        for back in range(ROWS - 2, -1, -1):
            total[ends] += step[ends - back]
    return total / np.float32(ROWS) > np.float32(LIMIT)
