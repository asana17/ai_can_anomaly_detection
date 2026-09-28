import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.sequence.repeated_signal import LAG, ROWS, WATCHED, hits

ALL = LAG + ROWS


def _rows(values, name="yaw_rate"):
    """Rows one after another with `name` at `values`, every other signal moving."""
    raw = np.tile(np.arange(len(values), dtype=float)[:, None], (1, len(SIGNALS)))
    raw[:, SIGNALS.index(name)] = values
    return raw, np.arange(len(values))


def _looped(rows):
    """A stretch of `LAG` values sent again and again."""
    return [0.01 * (i % LAG) for i in range(rows)]


def test_a_moving_signal_passes():
    raw, position = _rows(np.arange(ALL) * 0.01)
    assert not hits(raw, position).any()


def test_a_watched_signal_repeating_over_the_rows_is_flagged():
    for name in WATCHED:
        raw, position = _rows(_looped(ALL), name)
        assert hits(raw, position).tolist() == [False] * (ALL - 1) + [True]


def test_one_row_that_differs_breaks_it():
    values = _looped(ALL)
    values[-ROWS] += 1.0
    raw, position = _rows(values)
    assert not hits(raw, position).any()


def test_a_signal_not_watched_may_repeat():
    raw, position = _rows(_looped(ALL), "wheel_speed")
    assert not hits(raw, position).any()


def test_it_is_silent_until_the_rows_and_the_lag_come_before():
    raw, _ = _rows(_looped(ALL))
    position = np.r_[np.arange(ALL - 1), -1]
    assert not hits(raw, position).any()
