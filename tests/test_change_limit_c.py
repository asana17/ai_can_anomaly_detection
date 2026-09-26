import ctypes

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.sequence.change_limit import LIMITS, PERIOD, hits

ROWS = 100_000

WRAP = """#include "change_limit.h"

void run(const float *raw, const float *previous, size_t rows, bool *out)
{
\tRecentRows recent;
\tsize_t i;

\tfor (i = 0; i < rows; i++) {
\t\trecent_rows_clear(&recent);
\t\tif (previous != NULL) {
\t\t\trecent_rows_push(&recent, &previous[i * SIGNAL_COUNT]);
\t\t}
\t\tout[i] = change_limit_hits(&recent, &raw[i * SIGNAL_COUNT]);
\t}
}
"""


@pytest.fixture(scope="module")
def run(board_lib):
    function = board_lib(["rules", "signals"], WRAP).run
    function.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                         ctypes.c_void_p]
    function.restype = None
    return function


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


def test_the_c_port_matches_the_python_rule(run):
    raw, previous = (np.ascontiguousarray(a) for a in _pairs(np.random.default_rng(0)))
    got = np.zeros(ROWS, dtype=np.bool_)
    run(raw.ctypes.data, previous.ctypes.data, ROWS, got.ctypes.data)
    expected = hits(raw, previous)
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []


def test_a_row_with_no_row_before_matches_the_python_rule_on_nan(run):
    raw = np.ascontiguousarray(_pairs(np.random.default_rng(0))[0])
    got = np.ones(ROWS, dtype=np.bool_)
    run(raw.ctypes.data, None, ROWS, got.ctypes.data)
    expected = hits(raw, np.full_like(raw, np.nan))
    assert np.flatnonzero(got != expected).tolist() == []

