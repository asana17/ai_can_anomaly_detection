"""Flag a signal that holds one value over the last rows while the truck moves.

See rules/sequence/docs/frozen_signal.md.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

ROWS = 10       # the rows that hold one value, up to and including the row judged

# The signals that never hold one value over ROWS moving rows on normal data.
WATCHED = ("engine_speed", "input_shaft_speed", "yaw_rate", "lateral_accel")


def hits(raw: np.ndarray, position: np.ndarray) -> np.ndarray:
    """True where a `WATCHED` signal held one value over `ROWS` rows.

    `position` is each row's index, from 0, in its unbroken span of moving rows. A NaN
    compares false and never fires.
    """
    # A grid row holds float32.
    values = raw[:, [SIGNALS.index(name) for name in WATCHED]].astype(np.float32)
    flagged = np.zeros(len(raw), dtype=bool)
    ends = np.flatnonzero(np.asarray(position) >= ROWS - 1)
    if len(ends):
        held = np.ones((len(ends), len(WATCHED)), dtype=bool)
        for back in range(1, ROWS):
            held &= values[ends - back] == values[ends - back + 1]
        flagged[ends] = held.any(axis=1)
    return flagged
