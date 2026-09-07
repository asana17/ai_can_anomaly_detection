from rules.instant.reverse_speed import MAX_SPEED, NAMES, violations


def test_backing_up_slowly_passes():
    assert violations({"current_gear": -1, "wheel_speed": 3.0}) == []


def test_reverse_at_speed_is_flagged():
    assert violations({"current_gear": -1, "wheel_speed": 60.0}) == NAMES


def test_the_limit_itself_is_allowed():
    assert violations({"current_gear": -1, "wheel_speed": MAX_SPEED}) == []


def test_a_forward_gear_is_left_to_gear_ratio():
    assert violations({"current_gear": 12, "wheel_speed": 80.0}) == []


def test_neutral_is_not_reverse():
    assert violations({"current_gear": 0, "wheel_speed": 80.0}) == []


def test_it_says_nothing_until_both_have_arrived():
    assert violations({"current_gear": -1}) == []
    assert violations({"wheel_speed": 60.0}) == []
