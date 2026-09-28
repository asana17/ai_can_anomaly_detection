import ctypes

import numpy as np
import pytest

WRAP = """#include "recent_rows.h"
#include <stddef.h>

/* Push `pushes` rows whose first value counts up from 1, clearing before row `cleared`,
 * and give the first value of each row held, oldest first. */
uint32_t run(size_t pushes, size_t cleared, float *held)
{
\tRecentRows recent;
\tfloat row[SIGNAL_COUNT] = {0};
\tuint32_t index;
\tsize_t i;

\trecent_rows_clear(&recent);
\tfor (i = 0; i < pushes; i++) {
\t\tif (i == cleared) {
\t\t\trecent_rows_clear(&recent);
\t\t}
\t\trow[0] = (float)(i + 1);
\t\trecent_rows_push(&recent, row);
\t}
\tfor (index = 0; index < recent_rows_count(&recent); index++) {
\t\theld[index] = recent_rows_row(&recent, index)[0];
\t}
\treturn recent_rows_count(&recent);
}
"""


@pytest.fixture(scope="module")
def run(board_lib):
    function = board_lib(["rules", "signals"], WRAP).run
    function.argtypes = [ctypes.c_size_t, ctypes.c_size_t, ctypes.c_void_p]
    function.restype = ctypes.c_uint32
    return function


def _held(run, pushes, cleared=-1):
    """The rows held after the pushes, oldest first, by their first value."""
    held = np.zeros(32, np.float32)
    count = run(pushes, cleared if cleared >= 0 else pushes, held.ctypes.data)
    return held[:count].tolist()


def test_it_gives_the_rows_oldest_first(run):
    assert _held(run, 3) == [1.0, 2.0, 3.0]


def test_it_keeps_the_last_nineteen_when_full(run):
    assert _held(run, 22) == [float(n) for n in range(4, 23)]


def test_clear_forgets_the_rows_before(run):
    assert _held(run, 12, cleared=10) == [11.0, 12.0]
