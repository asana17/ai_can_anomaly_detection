import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.instant.pedal_conflict import PRESSED, hits

ROWS = 100_000


@pytest.fixture(scope="module")
def pedal_conflict_hits(board_rule):
    return board_rule("pedal_conflict", ["float"] * 2)


def _rows(rng):
    """Rows around the pressed threshold on both pedals, as float32 like the board's.

    NaN fills 1% of cells.
    """
    columns = {name: (rng.choice([0.0, PRESSED], ROWS) + rng.uniform(-0.5, 0.5, ROWS)
                      * rng.choice([0.0, 1e-6, 1.0], ROWS)).astype(np.float32)
               for name in ("accel_pedal", "brake_pedal")}
    raw = np.zeros((ROWS, len(SIGNALS)), dtype=np.float32)
    for name, column in columns.items():
        raw[:, SIGNALS.index(name)] = column
    raw[rng.random(raw.shape) < 0.01] = np.nan
    return raw


def test_the_c_port_matches_the_python_rule(pedal_conflict_hits):
    raw = _rows(np.random.default_rng(0))
    expected = hits(raw)
    columns = [raw[:, SIGNALS.index(name)] for name in
               ("accel_pedal", "brake_pedal")]
    got = np.array([pedal_conflict_hits(*(float(c[i]) for c in columns))
                    for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
