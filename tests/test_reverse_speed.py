import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.instant.reverse_speed import MAX_SPEED, hits


def _hit(values, **kwargs):
    """Whether the rule hits one row carrying `values`, every other signal at 0."""
    raw = np.zeros((1, len(SIGNALS)))
    for name, value in values.items():
        raw[0, SIGNALS.index(name)] = value
    return bool(hits(raw, **kwargs)[0])


def test_backing_up_slowly_passes():
    assert not _hit({"current_gear": -1, "wheel_speed": 3.0})


def test_reverse_at_speed_is_flagged():
    assert _hit({"current_gear": -1, "wheel_speed": 60.0})


def test_the_limit_itself_is_allowed():
    assert not _hit({"current_gear": -1, "wheel_speed": MAX_SPEED})


def test_a_forward_gear_is_left_to_gear_ratio():
    assert not _hit({"current_gear": 12, "wheel_speed": 80.0})


def test_neutral_is_not_reverse():
    assert not _hit({"current_gear": 0, "wheel_speed": 80.0})
