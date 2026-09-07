from rules.instant.stopped_shaft import MAX_SHAFT, NAMES, violations


def test_a_stopped_truck_with_a_stopped_shaft_passes():
    assert violations({"wheel_speed": 0.0, "output_shaft_speed": 10.0}) == []


def test_a_turning_shaft_with_the_truck_stopped_is_flagged():
    assert violations({"wheel_speed": 0.0, "output_shaft_speed": 900.0}) == NAMES


def test_the_limit_itself_is_allowed():
    assert violations({"wheel_speed": 0.0, "output_shaft_speed": MAX_SHAFT}) == []


def test_a_moving_truck_is_left_to_shaft_ratio():
    assert violations({"wheel_speed": 0.1, "output_shaft_speed": 5000.0}) == []


def test_it_says_nothing_until_both_have_arrived():
    assert violations({"wheel_speed": 0.0}) == []
