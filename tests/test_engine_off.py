from rules.instant.engine_off import MUST_BE_ZERO, violations


def test_a_stopped_engine_with_everything_still_passes():
    assert violations({"engine_speed": 0.0, "fuel_rate": 0.0, "engine_load": 0.0}) == []


def test_a_running_engine_is_not_this_rule():
    assert violations({"engine_speed": 600.0, "fuel_rate": 3.0}) == []


def test_every_driven_signal_is_reported_if_it_moves():
    for name in MUST_BE_ZERO:
        assert violations({"engine_speed": 0.0, name: 5.0}) == ["engine_speed", name]


def test_several_moving_at_once_are_all_reported():
    v = {"engine_speed": 0.0, "fuel_rate": 2.0, "engine_load": 30.0}
    assert violations(v) == ["engine_speed", "fuel_rate", "engine_load"]


def test_it_says_nothing_until_the_engine_speed_has_arrived():
    assert violations({"fuel_rate": 5.0}) == []
