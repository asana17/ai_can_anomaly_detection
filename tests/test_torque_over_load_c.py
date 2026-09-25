import ctypes

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.sequence.torque_over_load import LIMIT, hits

ROWS = 100_000

WRAP = """#include "rule_hits.h"
#include "torque_over_load.h"
#include <stddef.h>

void run(const float *raw, size_t signals, const uint32_t *no, const uint32_t *position,
\t size_t rows, bool *out)
{
\tTorqueOverLoad state;
\tsize_t i;

\ttorque_over_load_clear(&state);
\tfor(i = 0; i < rows; i++) {
\t\ttorque_over_load_put(&state, raw[i * signals + RULE_ACTUAL_ENGINE_TORQUE],
\t\t\t\t     raw[i * signals + RULE_ENGINE_LOAD], no[i], position[i]);
\t\tout[i] = torque_over_load_hits(&state);
\t}
}
"""


@pytest.fixture(scope="module")
def run(board_lib):
    function = board_lib(["rules", "float_ring"], WRAP).run
    function.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
                         ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
    function.restype = None
    return function


def _runs(rng):
    """Runs of 1 to 40 rows, torque minus load near the limit, NaN in 0.1% of cells.

    Each row's number follows the last, as the board numbers the rows it keeps.
    """
    lengths = rng.integers(1, 41, ROWS)
    lengths = lengths[:np.searchsorted(np.cumsum(lengths), ROWS)]
    position = np.concatenate([np.arange(n) for n in lengths]).astype(np.uint32)
    raw = rng.uniform(0.0, 100.0, (len(position), len(SIGNALS))).astype(np.float32)
    load = raw[:, SIGNALS.index("engine_load")]
    raw[:, SIGNALS.index("actual_engine_torque")] = (
        load + rng.normal(LIMIT, 2.0, len(load)).astype(np.float32))
    raw[rng.random(raw.shape) < 0.001] = np.nan
    return raw, position


def test_the_c_port_matches_the_python_rule(run):
    raw, position = _runs(np.random.default_rng(0))
    raw = np.ascontiguousarray(raw)
    no = np.arange(1, len(raw) + 1, dtype=np.uint32)
    got = np.zeros(len(raw), dtype=np.bool_)
    run(raw.ctypes.data, raw.shape[1], no.ctypes.data, position.ctypes.data, len(raw),
        got.ctypes.data)
    expected = hits(raw, position)
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []


def test_the_c_port_starts_over_after_a_missed_row(run):
    raw = np.zeros((15, len(SIGNALS)), dtype=np.float32)
    raw[:, SIGNALS.index("actual_engine_torque")] = 60.0
    raw[:, SIGNALS.index("engine_load")] = 50.0
    no = np.r_[1:6, 7:17].astype(np.uint32)
    position = np.r_[0:5, 6:16].astype(np.uint32)
    got = np.zeros(len(raw), dtype=np.bool_)
    run(raw.ctypes.data, raw.shape[1], no.ctypes.data, position.ctypes.data, len(raw),
        got.ctypes.data)
    assert np.flatnonzero(got).tolist() == [14]
