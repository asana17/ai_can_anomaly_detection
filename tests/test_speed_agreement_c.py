import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.instant.speed_agreement import MAX_DISAGREEMENT, hits

ROWS = 100_000


@pytest.fixture(scope="module")
def speed_agreement_hits(board_rule):
    return board_rule("speed_agreement", ["float"] * 2)


def _rows(rng):
    """Rows around the disagreement limit, as float32 like the board's.

    NaN fills 1% of cells.
    """
    wheel = rng.uniform(0.0, 100.0, ROWS).astype(np.float32)
    off = rng.uniform(-1.5, 1.5, ROWS) * MAX_DISAGREEMENT
    columns = {"wheel_speed": wheel, "tachograph_speed": (wheel + off).astype(np.float32)}
    raw = np.zeros((ROWS, len(SIGNALS)), dtype=np.float32)
    for name, column in columns.items():
        raw[:, SIGNALS.index(name)] = column
    raw[rng.random(raw.shape) < 0.01] = np.nan
    return raw


def test_the_c_port_matches_the_python_rule(speed_agreement_hits):
    raw = _rows(np.random.default_rng(0))
    expected = hits(raw)
    columns = [raw[:, SIGNALS.index(name)] for name in
               ("wheel_speed", "tachograph_speed")]
    got = np.array([speed_agreement_hits(*(float(c[i]) for c in columns))
                    for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
