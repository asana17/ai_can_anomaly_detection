from rules.shaft_ratio import BOUNDS, MIN_SPEED, violations

BOTH = ["output_shaft_speed", "wheel_speed"]


def test_a_normal_ratio_passes():
    assert violations({"output_shaft_speed": 15.25 * 80, "wheel_speed": 80.0}) == []


def test_a_shaft_turning_too_slowly_is_flagged():
    assert violations({"output_shaft_speed": 10.0 * 80, "wheel_speed": 80.0}) == BOTH


def test_a_shaft_turning_too_fast_is_flagged():
    assert violations({"output_shaft_speed": 25.0 * 80, "wheel_speed": 80.0}) == BOTH


def test_the_bounds_themselves_are_allowed():
    for bound in BOUNDS:
        assert violations({"output_shaft_speed": bound * 80, "wheel_speed": 80.0}) == []


def test_it_says_nothing_below_the_speed_gate():
    slow = {"output_shaft_speed": 1000.0, "wheel_speed": MIN_SPEED - 0.1}
    assert violations(slow) == []


def test_it_says_nothing_until_both_have_arrived():
    assert violations({"wheel_speed": 80.0}) == []
    assert violations({"output_shaft_speed": 1200.0}) == []


def test_the_bounds_can_be_tightened():
    values = {"output_shaft_speed": 16.5 * 80, "wheel_speed": 80.0}
    assert violations(values) == []
    assert violations(values, bounds=(14.0, 16.0)) == BOTH
