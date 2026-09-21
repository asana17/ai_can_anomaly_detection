import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.instant.reverse_speed import MAX_SPEED, hits

ROWS = 100_000


@pytest.fixture(scope="module")
def reverse_speed_hits(board_rule):
    return board_rule("reverse_speed", ["float"] * 2)


def _rows(rng):
    """Rows in and out of reverse around the speed limit, as float32 like the board's.

    NaN fills 1% of cells.
    """
    gear = rng.choice([-2.0, -1.0, 0.0, 1.0], ROWS)
    wheel = rng.uniform(0.0, 2.0, ROWS) * MAX_SPEED
    columns = {"current_gear": gear.astype(np.float32),
               "wheel_speed": wheel.astype(np.float32)}
    raw = np.zeros((ROWS, len(SIGNALS)), dtype=np.float32)
    for name, column in columns.items():
        raw[:, SIGNALS.index(name)] = column
    raw[rng.random(raw.shape) < 0.01] = np.nan
    return raw


def test_the_c_port_matches_the_python_rule(reverse_speed_hits):
    raw = _rows(np.random.default_rng(0))
    expected = hits(raw)
    columns = [raw[:, SIGNALS.index(name)] for name in
               ("current_gear", "wheel_speed")]
    got = np.array([reverse_speed_hits(*(float(c[i]) for c in columns))
                    for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
