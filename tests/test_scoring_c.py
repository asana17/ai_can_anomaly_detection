import ctypes

import numpy as np
import pytest

ROWS = 100_000
SIGNALS = 17


@pytest.fixture(scope="module")
def c_scoring_error(board_lib):
    """Build board/lib/scoring for this machine and give its `scoring_error`."""
    function = board_lib(["scoring"],
                         '#include "scoring_error.h"\n'
                         "float error(const float *scaled, const float *reconstructed,"
                         " size_t signals)\n"
                         "{\n\treturn scoring_error(scaled, reconstructed, signals);\n}\n"
                         ).error
    function.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                         ctypes.c_size_t]
    function.restype = ctypes.c_float
    return function


def test_the_c_port_matches_the_scorers_error(c_scoring_error):
    """The error the scorers in models/ take, up to the order the sum runs in."""
    rng = np.random.default_rng(0)
    fed = rng.normal(0.0, 1.0, (ROWS, SIGNALS)).astype(np.float32)
    got = (fed + rng.normal(0.0, 0.2, (ROWS, SIGNALS))).astype(np.float32)
    expected = ((got - fed) ** 2).mean(axis=1)
    row = ctypes.POINTER(ctypes.c_float)
    error = np.array([c_scoring_error(fed[i].ctypes.data_as(row),
                                      got[i].ctypes.data_as(row), SIGNALS)
                      for i in range(ROWS)], dtype=np.float32)
    np.testing.assert_allclose(error, expected, rtol=1e-6)
