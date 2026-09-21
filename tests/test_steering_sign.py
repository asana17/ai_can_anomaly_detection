import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.instant.steering_sign import MIN_YAW, hits


def _hit(values, **kwargs):
    """Whether the rule hits one row carrying `values`, every other signal at 0."""
    raw = np.zeros((1, len(SIGNALS)))
    for name, value in values.items():
        raw[0, SIGNALS.index(name)] = value
    return bool(hits(raw, **kwargs)[0])


GATE = 5.0


def _values(steering, yaw, speed=60.0):
    return {"steering_angle": steering, "yaw_rate": yaw, "wheel_speed": speed}


def test_turning_the_same_way_passes():
    assert not _hit(_values(0.5, 0.05), min_speed=GATE)
    assert not _hit(_values(-0.5, -0.05), min_speed=GATE)


def test_turning_opposite_ways_is_flagged():
    assert _hit(_values(0.5, -0.05), min_speed=GATE)


def test_it_stays_quiet_when_the_truck_is_going_straight():
    assert not _hit(_values(0.5, MIN_YAW - 0.001), min_speed=GATE)


def test_it_stays_quiet_below_the_speed_gate():
    assert not _hit(_values(0.5, -0.05, speed=GATE - 0.1), min_speed=GATE)
