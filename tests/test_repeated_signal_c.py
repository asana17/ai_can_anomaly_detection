import ctypes

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.sequence.repeated_signal import LAG, WATCHED, hits

WRAP = """#include "repeated_signal.h"
#include <stddef.h>

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
\t\tout[i] = repeated_signal_hits(&recent, row);
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
    """1 to 60 rows between gaps, some stretches of a watched signal sent again LAG rows
    on, some of them broken by one row or a NaN."""
    lengths = rng.integers(1, 61, 5_000)
    position = np.concatenate([np.arange(n) for n in lengths]).astype(np.uint32)
    raw = rng.uniform(0.0, 100.0, (len(position), len(SIGNALS))).astype(np.float32)
    for start in rng.integers(0, len(raw) - 40, 2_000):
        column = SIGNALS.index(WATCHED[rng.integers(len(WATCHED))])
        for i in range(start + LAG, start + LAG + rng.integers(5, 25)):
            raw[i, column] = raw[i - LAG, column]
        if rng.random() < 0.3:
            raw[start + LAG + rng.integers(0, 10), column] = np.nan
    return raw, position


def test_the_c_port_matches_the_python_rule(run):
    raw, position = _rows(np.random.default_rng(0))
    raw = np.ascontiguousarray(raw)
    got = np.zeros(len(raw), dtype=np.bool_)
    run(raw.ctypes.data, position.ctypes.data, len(raw), got.ctypes.data)
    expected = hits(raw, position)
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
