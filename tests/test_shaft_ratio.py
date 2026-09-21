import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.instant.shaft_ratio import BOUNDS, hits


def _hit(values, **kwargs):
    """Whether the rule hits one row carrying `values`, every other signal at 0."""
    raw = np.zeros((1, len(SIGNALS)))
    for name, value in values.items():
        raw[0, SIGNALS.index(name)] = value
    return bool(hits(raw, **kwargs)[0])


GATE = 5.0


def test_a_normal_ratio_passes():
    values = {"output_shaft_speed": 15.25 * 80, "wheel_speed": 80.0}
    assert not _hit(values, min_speed=GATE)


def test_a_shaft_turning_too_slowly_is_flagged():
    values = {"output_shaft_speed": 10.0 * 80, "wheel_speed": 80.0}
    assert _hit(values, min_speed=GATE)


def test_a_shaft_turning_too_fast_is_flagged():
    values = {"output_shaft_speed": 25.0 * 80, "wheel_speed": 80.0}
    assert _hit(values, min_speed=GATE)


def test_the_bounds_themselves_are_allowed():
    for bound in BOUNDS:
        values = {"output_shaft_speed": bound * 80, "wheel_speed": 80.0}
        assert not _hit(values, min_speed=GATE)


def test_it_says_nothing_below_the_speed_gate():
    slow = {"output_shaft_speed": 1000.0, "wheel_speed": GATE - 0.1}
    assert not _hit(slow, min_speed=GATE)


def test_the_bounds_can_be_tightened():
    values = {"output_shaft_speed": 16.5 * 80, "wheel_speed": 80.0}
    assert not _hit(values, min_speed=GATE)
    assert _hit(values, bounds=(14.0, 16.0), min_speed=GATE)
