import ctypes

import numpy as np
import pytest

WRAP = """#include "float_ring.h"
#include <stddef.h>

void run(uint32_t size, const float *value, const bool *clear, size_t rows, bool *full,
\t float *held)
{
\tfloat values[8];
\tFloatRing ring;
\tsize_t i;
\tuint32_t j;

\tfloat_ring_init(&ring, values, size);
\tfor(i = 0; i < rows; i++) {
\t\tif(clear[i]) {
\t\t\tfloat_ring_clear(&ring);
\t\t}
\t\tfloat_ring_put(&ring, value[i]);
\t\tfull[i] = float_ring_full(&ring);
\t\tfor(j = 0; j < ring.count; j++) {
\t\t\theld[i * size + j] = float_ring_get(&ring, j);
\t\t}
\t}
}
"""


@pytest.fixture(scope="module")
def run(board_lib):
    function = board_lib(["float_ring"], WRAP).run
    function.argtypes = [ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p,
                         ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p]
    function.restype = None
    return function


def _put(run, size, value, clear=None):
    """Whether the ring was full after each value, and what it held, oldest first."""
    value = np.asarray(value, np.float32)
    clear = np.zeros(len(value), np.bool_) if clear is None else np.asarray(clear)
    full = np.zeros(len(value), np.bool_)
    held = np.zeros((len(value), size), np.float32)
    run(size, value.ctypes.data, clear.ctypes.data, len(value), full.ctypes.data,
        held.ctypes.data)
    return full.tolist(), held.tolist()


def test_it_holds_the_last_size_values_oldest_first(run):
    full, held = _put(run, 3, [1.0, 2.0, 4.0, 8.0])
    assert full == [False, False, True, True]
    assert held == [[1.0, 0.0, 0.0], [1.0, 2.0, 0.0], [1.0, 2.0, 4.0], [2.0, 4.0, 8.0]]


def test_clear_empties_it(run):
    full, held = _put(run, 2, [1.0, 2.0, 4.0, 8.0], [False, False, True, False])
    assert full == [False, True, False, True]
    assert held[2:] == [[4.0, 0.0], [4.0, 8.0]]
