import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.instant.stopped_shaft import MAX_SHAFT, hits


def _hit(values, **kwargs):
    """Whether the rule hits one row carrying `values`, every other signal at 0."""
    raw = np.zeros((1, len(SIGNALS)))
    for name, value in values.items():
        raw[0, SIGNALS.index(name)] = value
    return bool(hits(raw, **kwargs)[0])


def test_a_stopped_truck_with_a_stopped_shaft_passes():
    assert not _hit({"wheel_speed": 0.0, "output_shaft_speed": 10.0})


def test_a_turning_shaft_with_the_truck_stopped_is_flagged():
    assert _hit({"wheel_speed": 0.0, "output_shaft_speed": 900.0})


def test_the_limit_itself_is_allowed():
    assert not _hit({"wheel_speed": 0.0, "output_shaft_speed": MAX_SHAFT})


def test_a_moving_truck_is_left_to_shaft_ratio():
    assert not _hit({"wheel_speed": 0.1, "output_shaft_speed": 5000.0})


def test_a_rolling_tachograph_leaves_it_to_speed_agreement():
    assert not _hit({"wheel_speed": 0.0, "tachograph_speed": 3.0,
                     "output_shaft_speed": 900.0})
