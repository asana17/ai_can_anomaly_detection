import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.sequence.frozen_signal import ROWS, WATCHED, hits


def _rows(values, name="yaw_rate"):
    """Rows one after another with `name` at `values`, every other signal moving."""
    raw = np.tile(np.arange(len(values), dtype=float)[:, None], (1, len(SIGNALS)))
    raw[:, SIGNALS.index(name)] = values
    return raw, np.arange(len(values))


def test_a_moving_signal_passes():
    raw, position = _rows(np.arange(ROWS) * 0.01)
    assert not hits(raw, position).any()


def test_a_watched_signal_held_over_the_rows_is_flagged():
    for name in WATCHED:
        raw, position = _rows([0.2] * ROWS, name)
        assert hits(raw, position).tolist() == [False] * (ROWS - 1) + [True]


def test_a_signal_not_watched_may_hold():
    raw, position = _rows([50.0] * ROWS, "wheel_speed")
    assert not hits(raw, position).any()


def test_it_is_silent_until_nine_rows_come_before():
    raw, _ = _rows([0.2] * (2 * ROWS - 1))
    position = np.r_[np.arange(ROWS), np.arange(ROWS - 1)]
    expected = [False] * (ROWS - 1) + [True] + [False] * (ROWS - 1)
    assert hits(raw, position).tolist() == expected


def test_a_nan_held_never_fires():
    raw, position = _rows([np.nan] * ROWS)
    assert not hits(raw, position).any()
