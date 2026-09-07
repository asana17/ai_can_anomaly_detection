from preprocess.frames.spn_spec import SPEC
from rules.instant.range_check import LIMITS, violations


def test_a_normal_reading_passes():
    assert violations({"engine_speed": 1200.0, "wheel_speed": 80.0}) == []


def test_above_the_maximum_is_flagged():
    assert violations({"wheel_speed": 300.0}) == ["wheel_speed"]


def test_below_the_minimum_is_flagged():
    assert violations({"steering_angle": -40.0}) == ["steering_angle"]


def test_the_limits_themselves_are_allowed():
    low, high = LIMITS["brake_pedal"]
    assert violations({"brake_pedal": low}) == []
    assert violations({"brake_pedal": high}) == []


def test_a_name_with_no_definition_is_ignored():
    assert violations({"not_a_signal": 1e9}) == []


def test_every_decodable_signal_has_limits():
    assert LIMITS.keys() == {d.name for defs in SPEC.values() for d in defs}
