import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.instant.shaft_ratio import BOUNDS, hits

GATE = 5.0
ROWS = 100_000


@pytest.fixture(scope="module")
def shaft_ratio_hits(board_rule):
    return board_rule("shaft_ratio", ["float"] * 3)


def _rows(rng):
    """Rows around the gate and both bounds, as float32 like the board's.

    NaN fills 1% of cells.
    """
    wheel = rng.uniform(0.0, 100.0, ROWS).astype(np.float32)
    ratio = rng.choice(BOUNDS, ROWS) * rng.uniform(0.9, 1.1, ROWS)
    shaft = (wheel * ratio).astype(np.float32)
    raw = np.zeros((ROWS, len(SIGNALS)), dtype=np.float32)
    raw[:, SIGNALS.index("output_shaft_speed")] = shaft
    raw[:, SIGNALS.index("wheel_speed")] = wheel
    raw[rng.random(raw.shape) < 0.01] = np.nan
    return raw


def test_the_c_port_matches_the_python_rule(shaft_ratio_hits):
    raw = _rows(np.random.default_rng(0))
    expected = hits(raw, min_speed=GATE)
    columns = [raw[:, SIGNALS.index(name)] for name in
               ("output_shaft_speed", "wheel_speed")]
    got = np.array([shaft_ratio_hits(*(float(c[i]) for c in columns), GATE)
                    for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
