import ctypes

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.rate.change_limit import LIMITS, PERIOD, hits

ROWS = 100_000


@pytest.fixture(scope="module")
def change_limit_hits(board_rule):
    return board_rule("change_limit", ["const float *", "const float *"])


def _pairs(rng):
    """Rows and the rows before them, each limited signal a step near its limit away.

    The steps fall either side of the limit, a few on it. NaN fills 0.1% of cells.
    """
    previous = rng.uniform(-100.0, 100.0, (ROWS, len(SIGNALS)))
    raw = previous.copy()
    for name, limit in LIMITS.items():
        factor = rng.choice([1.0, 1.0 - 1e-6, 1.0 + 1e-6, 0.5], ROWS,
                            p=[0.1, 0.4, 0.001, 0.499])
        sign = rng.choice([-1.0, 1.0], ROWS)
        raw[:, SIGNALS.index(name)] += sign * factor * limit * PERIOD
    raw, previous = raw.astype(np.float32), previous.astype(np.float32)
    raw[rng.random(raw.shape) < 0.001] = np.nan
    previous[rng.random(previous.shape) < 0.001] = np.nan
    return raw, previous


def test_the_c_port_matches_the_python_rule(change_limit_hits):
    raw, previous = (np.ascontiguousarray(a) for a in _pairs(np.random.default_rng(0)))
    expected = hits(raw, previous)
    row = ctypes.POINTER(ctypes.c_float)
    got = np.array([change_limit_hits(raw[i].ctypes.data_as(row),
                                      previous[i].ctypes.data_as(row))
                    for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []

