from rules.rate.change_limit import LIMITS, violations


def test_a_normal_move_passes():
    assert violations({"wheel_speed": 80.0}, {"wheel_speed": 79.0}, 0.1) == []


def test_a_jump_too_far_for_the_time_is_flagged():
    assert violations({"wheel_speed": 80.0}, {"wheel_speed": 20.0}, 0.1) == ["wheel_speed"]


def test_the_same_jump_over_enough_time_passes():
    assert violations({"wheel_speed": 80.0}, {"wheel_speed": 20.0}, 10.0) == []


def test_the_limit_itself_is_allowed():
    limit = LIMITS["wheel_speed"]
    assert violations({"wheel_speed": limit}, {"wheel_speed": 0.0}, 1.0) == []


def test_several_signals_are_all_reported():
    now = {"wheel_speed": 80.0, "yaw_rate": 1.0}
    before = {"wheel_speed": 20.0, "yaw_rate": 0.0}
    assert violations(now, before, 0.1) == ["yaw_rate", "wheel_speed"]


def test_a_signal_with_no_limit_is_ignored():
    assert violations({"engine_speed": 3000.0}, {"engine_speed": 600.0}, 0.02) == []


def test_it_says_nothing_without_a_previous_reading():
    assert violations({"wheel_speed": 80.0}, {}, 0.1) == []


def test_it_says_nothing_when_no_time_has_passed():
    assert violations({"wheel_speed": 80.0}, {"wheel_speed": 20.0}, 0.0) == []
