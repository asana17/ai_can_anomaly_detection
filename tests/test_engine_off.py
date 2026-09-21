import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.instant.engine_off import MUST_BE_ZERO, hits


def _hit(values, **kwargs):
    """Whether the rule hits one row carrying `values`, every other signal at 0."""
    raw = np.zeros((1, len(SIGNALS)))
    for name, value in values.items():
        raw[0, SIGNALS.index(name)] = value
    return bool(hits(raw, **kwargs)[0])


def test_a_stopped_engine_with_everything_still_passes():
    assert not _hit({"engine_speed": 0.0, "fuel_rate": 0.0, "engine_load": 0.0})


def test_a_running_engine_is_not_this_rule():
    assert not _hit({"engine_speed": 600.0, "fuel_rate": 3.0})


def test_every_driven_signal_is_flagged_if_it_moves():
    for name in MUST_BE_ZERO:
        assert _hit({"engine_speed": 0.0, name: 5.0})


def test_several_moving_at_once_are_flagged():
    assert _hit({"engine_speed": 0.0, "fuel_rate": 2.0, "engine_load": 30.0})
