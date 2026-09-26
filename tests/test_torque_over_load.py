import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.sequence.torque_over_load import LIMIT, ROWS, hits


def _rows(torque, load):
    """Rows one after another with this torque and load, every other signal at 0."""
    raw = np.zeros((len(torque), len(SIGNALS)))
    raw[:, SIGNALS.index("actual_engine_torque")] = torque
    raw[:, SIGNALS.index("engine_load")] = load
    return raw, np.arange(len(torque))


def test_load_above_torque_passes():
    raw, position = _rows([40.0] * ROWS, [80.0] * ROWS)
    assert not hits(raw, position).any()


def test_torque_above_load_over_the_rows_is_flagged():
    raw, position = _rows([60.0] * ROWS, [50.0] * ROWS)
    assert hits(raw, position).tolist() == [False] * (ROWS - 1) + [True]


def test_the_limit_itself_is_allowed():
    raw, position = _rows([50.0 + LIMIT] * ROWS, [50.0] * ROWS)
    assert not hits(raw, position).any()


def test_one_row_far_above_is_averaged_out():
    torque = [50.0] * ROWS
    torque[-1] = 50.0 + LIMIT * ROWS * 0.9
    raw, position = _rows(torque, [50.0] * ROWS)
    assert not hits(raw, position).any()


def test_it_is_silent_until_nine_rows_come_before():
    raw, _ = _rows([60.0] * (2 * ROWS - 1), [50.0] * (2 * ROWS - 1))
    position = np.r_[np.arange(ROWS), np.arange(ROWS - 1)]
    expected = [False] * (ROWS - 1) + [True] + [False] * (ROWS - 1)
    assert hits(raw, position).tolist() == expected


def test_a_nan_in_the_window_never_fires():
    torque = [60.0] * (ROWS + 1)
    torque[1] = np.nan
    raw, position = _rows(torque, [50.0] * (ROWS + 1))
    assert hits(raw, position).tolist() == [False] * (ROWS + 1)
