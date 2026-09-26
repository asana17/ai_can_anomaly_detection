import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.sequence.change_limit import LIMITS, PERIOD, hits


def _rows(*values):
    """One row for each of `values`, every other signal at 0."""
    raw = np.zeros((len(values), len(SIGNALS)))
    for row, named in enumerate(values):
        for name, value in named.items():
            raw[row, SIGNALS.index(name)] = value
    return raw


def _hit(now, before):
    return bool(hits(_rows(before, now), np.arange(2))[1])


def test_a_normal_move_passes():
    assert not _hit({"wheel_speed": 80.0}, {"wheel_speed": 79.0})


def test_a_jump_too_far_for_a_tick_is_flagged():
    assert _hit({"wheel_speed": 80.0}, {"wheel_speed": 70.0})


def test_a_fall_is_flagged_as_a_rise_is():
    assert _hit({"wheel_speed": 70.0}, {"wheel_speed": 80.0})


def test_the_limit_itself_is_allowed():
    step = LIMITS["wheel_speed"] * PERIOD
    assert not _hit({"wheel_speed": 80.0 + step}, {"wheel_speed": 80.0})


def test_a_signal_with_no_limit_is_ignored():
    assert not _hit({"input_shaft_speed": 3000.0}, {"input_shaft_speed": 600.0})


def test_each_row_is_judged_against_its_own_row_before():
    raw = _rows({"yaw_rate": 0.0}, {"yaw_rate": 0.02}, {"yaw_rate": -0.05})
    assert hits(raw, np.arange(3)).tolist() == [False, False, True]


def test_the_first_row_of_a_span_is_not_compared_with_the_row_above():
    raw = _rows({"wheel_speed": 70.0}, {"wheel_speed": 80.0}, {"wheel_speed": 70.0})
    assert hits(raw, np.array([0, 0, -1])).tolist() == [False, False, False]
