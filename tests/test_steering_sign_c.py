import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.instant.steering_sign import MIN_YAW, hits

ROWS = 100_000
GATE = 5.0


@pytest.fixture(scope="module")
def steering_sign_hits(board_rule):
    return board_rule("steering_sign", ["float"] * 4)


def _rows(rng):
    """Rows around the speed gate and the yaw floor, as float32 like the board's.

    NaN fills 1% of cells.
    """
    columns = {"steering_angle": rng.uniform(-1.0, 1.0, ROWS).astype(np.float32),
               "yaw_rate": (rng.uniform(-3.0, 3.0, ROWS) * MIN_YAW).astype(np.float32),
               "wheel_speed": rng.uniform(0.0, 2 * GATE, ROWS).astype(np.float32)}
    columns["steering_angle"][rng.random(ROWS) < 0.05] = 0.0
    raw = np.zeros((ROWS, len(SIGNALS)), dtype=np.float32)
    for name, column in columns.items():
        raw[:, SIGNALS.index(name)] = column
    raw[rng.random(raw.shape) < 0.01] = np.nan
    return raw


def test_the_c_port_matches_the_python_rule(steering_sign_hits):
    raw = _rows(np.random.default_rng(0))
    expected = hits(raw, min_speed=GATE)
    columns = [raw[:, SIGNALS.index(name)] for name in
               ("steering_angle", "yaw_rate", "wheel_speed")]
    got = np.array([steering_sign_hits(*(float(c[i]) for c in columns), GATE)
                    for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
