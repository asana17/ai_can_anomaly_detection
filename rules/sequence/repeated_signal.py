"""Flag a signal that repeats what it read LAG rows before, over the last rows.

See rules/sequence/docs/repeated_signal.md.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

LAG = 10        # the rows back the value is compared with
ROWS = 10       # the rows that repeat, up to and including the row judged

# The signals that never repeat over ROWS moving rows on normal data.
WATCHED = ("engine_speed", "input_shaft_speed", "yaw_rate", "lateral_accel")


def hits(raw: np.ndarray, position: np.ndarray) -> np.ndarray:
    """True where a `WATCHED` signal read what it read `LAG` rows before, on each of
    `ROWS` rows.

    `position` is each row's index, from 0, in its unbroken span of moving rows. A NaN
    compares false and never fires.
    """
    # A grid row holds float32.
    values = raw[:, [SIGNALS.index(name) for name in WATCHED]].astype(np.float32)
    flagged = np.zeros(len(raw), dtype=bool)
    ends = np.flatnonzero(np.asarray(position) >= LAG + ROWS - 1)
    if len(ends):
        repeated = np.ones((len(ends), len(WATCHED)), dtype=bool)
        for back in range(ROWS):
            repeated &= values[ends - back] == values[ends - back - LAG]
        flagged[ends] = repeated.any(axis=1)
    return flagged
