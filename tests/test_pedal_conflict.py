import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.instant.pedal_conflict import PRESSED, hits


def _hit(values, **kwargs):
    """Whether the rule hits one row carrying `values`, every other signal at 0."""
    raw = np.zeros((1, len(SIGNALS)))
    for name, value in values.items():
        raw[0, SIGNALS.index(name)] = value
    return bool(hits(raw, **kwargs)[0])


def test_one_pedal_at_a_time_passes():
    assert not _hit({"accel_pedal": 40.0, "brake_pedal": 0.0})
    assert not _hit({"accel_pedal": 0.0, "brake_pedal": 30.0})


def test_both_pressed_is_flagged():
    assert _hit({"accel_pedal": 30.0, "brake_pedal": 20.0})


def test_a_pedal_resting_on_its_stop_does_not_count():
    assert not _hit({"accel_pedal": PRESSED, "brake_pedal": PRESSED})
