import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.instant.engine_off import MUST_BE_ZERO, hits

ROWS = 100_000


@pytest.fixture(scope="module")
def engine_off_hits(board_rule):
    return board_rule("engine_off", ["float"] * 7)


def _rows(rng):
    """Rows with each signal mostly zero, as float32 like the board's.

    NaN fills 1% of cells.
    """
    columns = {name: np.where(rng.random(ROWS) < 0.9, 0.0, rng.uniform(-5.0, 5.0, ROWS))
               .astype(np.float32) for name in ["engine_speed", *MUST_BE_ZERO]}
    raw = np.zeros((ROWS, len(SIGNALS)), dtype=np.float32)
    for name, column in columns.items():
        raw[:, SIGNALS.index(name)] = column
    raw[rng.random(raw.shape) < 0.01] = np.nan
    return raw


def test_the_c_port_matches_the_python_rule(engine_off_hits):
    raw = _rows(np.random.default_rng(0))
    expected = hits(raw)
    columns = [raw[:, SIGNALS.index(name)] for name in
               ("engine_speed", *MUST_BE_ZERO)]
    got = np.array([engine_off_hits(*(float(c[i]) for c in columns))
                    for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
