from rules.instant.speed_agreement import MAX_DISAGREEMENT, violations


def test_two_speeds_that_agree_pass():
    assert violations({"wheel_speed": 80.0, "tachograph_speed": 80.4}) == []


def test_a_disagreement_flags_both():
    assert violations({"wheel_speed": 80.0, "tachograph_speed": 40.0}) == [
        "wheel_speed", "tachograph_speed"]


def test_the_limit_itself_is_allowed():
    assert violations({"wheel_speed": 80.0, "tachograph_speed": 80.0 + MAX_DISAGREEMENT}) == []


def test_it_says_nothing_until_both_have_arrived():
    assert violations({"wheel_speed": 80.0}) == []
    assert violations({"tachograph_speed": 80.0}) == []
    assert violations({}) == []


def test_the_limit_can_be_tightened():
    values = {"wheel_speed": 80.0, "tachograph_speed": 81.0}
    assert violations(values) == []
    assert violations(values, limit=0.5) == ["wheel_speed", "tachograph_speed"]
