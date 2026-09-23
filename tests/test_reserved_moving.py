import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.instant.reserved_moving import hits


def _hit(values):
    """Whether the rule hits one row carrying `values`, every other signal at 0."""
    raw = np.zeros((1, len(SIGNALS)))
    for name, value in values.items():
        raw[0, SIGNALS.index(name)] = value
    return bool(hits(raw)[0])


def test_a_reserved_value_while_moving_is_flagged():
    assert _hit({"wheel_speed": 80.0, "tachograph_speed": 80.0, "fuel_rate": np.nan})


def test_a_reserved_value_while_stopped_passes():
    assert not _hit({"wheel_speed": 0.0, "fuel_rate": np.nan})


def test_a_reserved_wheel_speed_is_caught_by_the_tachograph():
    assert _hit({"wheel_speed": np.nan, "tachograph_speed": 80.0})


def test_a_moving_row_with_no_reserved_value_passes():
    assert not _hit({"wheel_speed": 80.0, "tachograph_speed": 80.0})


def test_creeping_counts_as_moving():
    assert _hit({"wheel_speed": 0.5, "tachograph_speed": 0.5, "fuel_rate": np.nan})


def test_both_speeds_reserved_are_caught_by_the_shaft():
    assert _hit({"wheel_speed": np.nan, "tachograph_speed": np.nan,
                 "output_shaft_speed": 1200.0})
