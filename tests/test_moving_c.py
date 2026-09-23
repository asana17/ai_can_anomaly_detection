import ctypes

import numpy as np
import pytest

from common.settings import SplitSettings
from preprocess.features.moving import moving
from preprocess.features.signal_state import SIGNALS

ROWS = 100_000


@pytest.fixture(scope="module")
def c_moving(board_lib):
    """Build board/lib/moving for this machine and give its `moving`."""
    function = board_lib(["moving"],
                         '#include "moving.h"\n'
                         "bool is_moving(const float *row, float min_speed)\n"
                         "{\n\treturn moving(row, min_speed);\n}\n").is_moving
    function.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_float]
    function.restype = ctypes.c_bool
    return function


def test_the_c_port_matches_the_python(c_moving):
    """Rows around MIN_SPEED, as float32 like the board's. NaN fills 1% of cells."""
    rng = np.random.default_rng(0)
    min_speed = SplitSettings().MIN_SPEED
    raw = rng.uniform(0.0, 2.0, (ROWS, len(SIGNALS))).astype(np.float32) * min_speed
    raw[rng.random(ROWS) < 0.02, SIGNALS.index("wheel_speed")] = min_speed
    raw[rng.random(raw.shape) < 0.01] = np.nan
    expected = moving(raw, min_speed=min_speed)
    row = ctypes.POINTER(ctypes.c_float)
    got = np.array([c_moving(raw[i].ctypes.data_as(row), min_speed) for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
