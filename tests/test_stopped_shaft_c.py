import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.instant.stopped_shaft import MAX_SHAFT, hits

ROWS = 100_000


@pytest.fixture(scope="module")
def stopped_shaft_hits(board_rule):
    return board_rule("stopped_shaft", ["float"] * 3)


def _rows(rng):
    """Rows with both speeds mostly stopped, as float32 like the board's.

    NaN fills 1% of cells.
    """
    columns = {name: np.where(rng.random(ROWS) < 0.7, 0.0, rng.uniform(0.0, 5.0, ROWS))
               .astype(np.float32) for name in ("wheel_speed", "tachograph_speed")}
    columns["output_shaft_speed"] = (rng.uniform(0.0, 2.0, ROWS) * MAX_SHAFT
                                     ).astype(np.float32)
    raw = np.zeros((ROWS, len(SIGNALS)), dtype=np.float32)
    for name, column in columns.items():
        raw[:, SIGNALS.index(name)] = column
    raw[rng.random(raw.shape) < 0.01] = np.nan
    return raw


def test_the_c_port_matches_the_python_rule(stopped_shaft_hits):
    raw = _rows(np.random.default_rng(0))
    expected = hits(raw)
    columns = [raw[:, SIGNALS.index(name)] for name in
               ("wheel_speed", "tachograph_speed", "output_shaft_speed")]
    got = np.array([stopped_shaft_hits(*(float(c[i]) for c in columns))
                    for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
