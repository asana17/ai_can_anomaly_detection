import ctypes

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.sequence.change_limit import LIMITS, PERIOD, hits

WRAP = """#include "change_limit.h"

void run(const float *raw, const uint32_t *position, size_t rows, bool *out)
{
\tRecentRows recent;
\tconst float *row;
\tsize_t i;

\trecent_rows_clear(&recent);
\tfor (i = 0; i < rows; i++) {
\t\trow = &raw[i * SIGNAL_COUNT];
\t\tif (position[i] == 0u) {
\t\t\trecent_rows_clear(&recent);
\t\t}
\t\tout[i] = change_limit_hits(&recent, row);
\t\trecent_rows_push(&recent, row);
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


def _rows(rng):
    """1 to 40 rows between gaps, each limited signal a step near its limit from the row
    before.

    The steps fall either side of the limit, a few on it. NaN fills 0.1% of cells.
    """
    lengths = rng.integers(1, 41, 5_000)
    position = np.concatenate([np.arange(n) for n in lengths]).astype(np.uint32)
    start = rng.uniform(-100.0, 100.0, (1, len(SIGNALS)))
    raw = np.repeat(start, len(position), axis=0)
    for name, limit in LIMITS.items():
        factor = rng.choice([1.0, 1.0 - 1e-6, 1.0 + 1e-6, 0.5], len(position),
                            p=[0.1, 0.4, 0.001, 0.499])
        sign = rng.choice([-1.0, 1.0], len(position))
        column = SIGNALS.index(name)
        raw[:, column] += np.cumsum(sign * factor * limit * PERIOD)
    raw = raw.astype(np.float32)
    raw[rng.random(raw.shape) < 0.001] = np.nan
    return raw, position


def test_the_c_port_matches_the_python_rule(run):
    raw, position = _rows(np.random.default_rng(0))
    raw = np.ascontiguousarray(raw)
    got = np.zeros(len(raw), dtype=np.bool_)
    run(raw.ctypes.data, position.ctypes.data, len(raw), got.ctypes.data)
    expected = hits(raw, position)
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
