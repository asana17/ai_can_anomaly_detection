import ctypes

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.instant.reserved_moving import hits

ROWS = 100_000


@pytest.fixture(scope="module")
def reserved_moving_hits(board_rule):
    return board_rule("reserved_moving", ["const float *", "float", "float"])


def _rows(rng):
    """Rows with each speed at 0 half the time, as float32 like the board's.

    NaN fills 1% of cells.
    """
    raw = np.where(rng.random((ROWS, len(SIGNALS))) < 0.5, 0.0,
                   rng.uniform(0.0, 10.0, (ROWS, len(SIGNALS))))
    raw[rng.random(raw.shape) < 0.01] = np.nan
    return np.ascontiguousarray(raw.astype(np.float32))


def test_the_c_port_matches_the_python_rule(reserved_moving_hits):
    raw = _rows(np.random.default_rng(0))
    expected = hits(raw)
    row = ctypes.POINTER(ctypes.c_float)
    wheel = SIGNALS.index("wheel_speed")
    tachograph = SIGNALS.index("tachograph_speed")
    got = np.array([reserved_moving_hits(raw[i].ctypes.data_as(row), float(raw[i, wheel]),
                                         float(raw[i, tachograph]))
                    for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
