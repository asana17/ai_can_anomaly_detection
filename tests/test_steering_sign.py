from rules.steering_sign import MIN_SPEED, MIN_YAW, NAMES, violations


def _values(steering, yaw, speed=60.0):
    return {"steering_angle": steering, "yaw_rate": yaw, "wheel_speed": speed}


def test_turning_the_same_way_passes():
    assert violations(_values(0.5, 0.05)) == []
    assert violations(_values(-0.5, -0.05)) == []


def test_turning_opposite_ways_is_flagged():
    assert violations(_values(0.5, -0.05)) == NAMES


def test_it_stays_quiet_when_the_truck_is_going_straight():
    assert violations(_values(0.5, MIN_YAW - 0.001)) == []


def test_it_stays_quiet_below_the_speed_gate():
    assert violations(_values(0.5, -0.05, speed=MIN_SPEED - 0.1)) == []


def test_it_says_nothing_until_every_signal_has_arrived():
    v = _values(0.5, -0.05)
    for name in v:
        assert violations({k: x for k, x in v.items() if k != name}) == []
