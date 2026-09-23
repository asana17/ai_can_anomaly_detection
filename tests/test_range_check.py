import numpy as np

from preprocess.features.signal_state import SIGNALS
from preprocess.frames.spn_spec import SPEC
from rules.instant.range_check import LIMITS, hits


def _hit(values, **kwargs):
    """Whether the rule hits one row carrying `values`, every other signal at 0."""
    raw = np.zeros((1, len(SIGNALS)))
    for name, value in values.items():
        raw[0, SIGNALS.index(name)] = value
    return bool(hits(raw, **kwargs)[0])


def test_a_normal_reading_passes():
    assert not _hit({"engine_speed": 1200.0, "wheel_speed": 80.0})


def test_above_the_maximum_is_flagged():
    assert _hit({"wheel_speed": 300.0})


def test_below_the_minimum_is_flagged():
    assert _hit({"steering_angle": -40.0})


def test_the_limits_themselves_are_allowed():
    low, high = LIMITS["brake_pedal"]
    assert not _hit({"brake_pedal": low})
    assert not _hit({"brake_pedal": high})


def test_the_lowest_decodable_value_passes_as_float32():
    # raw 0 decodes to the offset, which float32 rounds below the float64 minimum
    for name in ("steering_angle", "yaw_rate", "lateral_accel"):
        raw = np.zeros((1, len(SIGNALS)), dtype=np.float32)
        raw[0, SIGNALS.index(name)] = LIMITS[name][0]
        assert not hits(raw)[0]


def test_a_nan_is_not_flagged():
    assert not _hit({"wheel_speed": float("nan")})


def test_every_decodable_signal_has_limits():
    assert LIMITS.keys() == {d.name for defs in SPEC.values() for d in defs}
