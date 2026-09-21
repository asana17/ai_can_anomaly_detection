import ctypes

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.instant.range_check import LIMITS, hits

ROWS = 100_000


@pytest.fixture(scope="module")
def range_check_hits(board_rule):
    return board_rule("range_check", ["const float *"])


def _rows(rng):
    """Rows near an end of each range, as float32 like the board's.

    A few cells sit on an end or past it. NaN fills 0.1% of cells.
    """
    low = np.array([LIMITS[name][0] for name in SIGNALS])
    high = np.array([LIMITS[name][1] for name in SIGNALS])
    end = np.where(rng.random((ROWS, len(SIGNALS))) < 0.5, low, high)
    inward = np.where(end == low, 1.0, -1.0)
    # the float32 nearest an end can fall either side of it
    step = rng.choice([0.0, 1e-3, 0.5], (ROWS, len(SIGNALS)), p=[0.02, 0.49, 0.49])
    outward = rng.random((ROWS, len(SIGNALS))) < 0.004
    raw = (end + np.where(outward, -inward, inward) * step * (high - low)).astype(np.float32)
    raw[rng.random(raw.shape) < 0.001] = np.nan
    return raw


def test_the_c_port_matches_the_python_rule(range_check_hits):
    raw = np.ascontiguousarray(_rows(np.random.default_rng(0)))
    expected = hits(raw)
    row = ctypes.POINTER(ctypes.c_float)
    got = np.array([range_check_hits(raw[i].ctypes.data_as(row)) for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
