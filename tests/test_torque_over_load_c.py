import ctypes

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.sequence.torque_over_load import LIMIT, hits

WRAP = """#include "torque_over_load.h"
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
\t\tout[i] = torque_over_load_hits(&recent, row);
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
    """1 to 40 rows between gaps, torque minus load near the limit, some cells NaN."""
    lengths = rng.integers(1, 41, 10_000)
    position = np.concatenate([np.arange(n) for n in lengths]).astype(np.uint32)
    raw = rng.uniform(0.0, 100.0, (len(position), len(SIGNALS))).astype(np.float32)
    torque, load = SIGNALS.index("actual_engine_torque"), SIGNALS.index("engine_load")
    raw[:, torque] = raw[:, load] + rng.normal(LIMIT, 2.0, len(raw)).astype(np.float32)
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
