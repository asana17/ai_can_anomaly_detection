import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.rate.change_limit import LIMITS, PERIOD, hits


def _rows(values):
    """One row carrying `values`, every other signal at 0."""
    raw = np.zeros((1, len(SIGNALS)))
    for name, value in values.items():
        raw[0, SIGNALS.index(name)] = value
    return raw


def _hit(now, before):
    return bool(hits(_rows(now), _rows(before))[0])


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


def test_it_says_nothing_without_a_row_before():
    before = np.full((1, len(SIGNALS)), np.nan)
    assert not hits(_rows({"wheel_speed": 80.0}), before)[0]


def test_each_row_is_judged_against_its_own_row_before():
    raw = np.vstack([_rows({"yaw_rate": 0.02}), _rows({"yaw_rate": 0.02})])
    before = np.vstack([_rows({"yaw_rate": 0.0}), _rows({"yaw_rate": -0.05})])
    assert hits(raw, before).tolist() == [False, True]
