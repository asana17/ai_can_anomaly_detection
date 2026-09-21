import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.instant.speed_agreement import MAX_DISAGREEMENT, hits


def _hit(values, **kwargs):
    """Whether the rule hits one row carrying `values`, every other signal at 0."""
    raw = np.zeros((1, len(SIGNALS)))
    for name, value in values.items():
        raw[0, SIGNALS.index(name)] = value
    return bool(hits(raw, **kwargs)[0])


def test_two_speeds_that_agree_pass():
    assert not _hit({"wheel_speed": 80.0, "tachograph_speed": 80.4})


def test_a_disagreement_is_flagged():
    assert _hit({"wheel_speed": 80.0, "tachograph_speed": 40.0})


def test_the_limit_itself_is_allowed():
    assert not _hit({"wheel_speed": 80.0, "tachograph_speed": 80.0 + MAX_DISAGREEMENT})


def test_the_limit_can_be_tightened():
    values = {"wheel_speed": 80.0, "tachograph_speed": 81.0}
    assert not _hit(values)
    assert _hit(values, limit=0.5)
