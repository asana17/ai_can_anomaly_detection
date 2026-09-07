from rules.instant.pedal_conflict import NAMES, PRESSED, violations


def test_one_pedal_at_a_time_passes():
    assert violations({"accel_pedal": 40.0, "brake_pedal": 0.0}) == []
    assert violations({"accel_pedal": 0.0, "brake_pedal": 30.0}) == []


def test_both_pressed_is_flagged():
    assert violations({"accel_pedal": 30.0, "brake_pedal": 20.0}) == NAMES


def test_a_pedal_resting_on_its_stop_does_not_count():
    assert violations({"accel_pedal": PRESSED, "brake_pedal": PRESSED}) == []


def test_it_says_nothing_until_both_have_arrived():
    assert violations({"accel_pedal": 30.0}) == []
