import ctypes
import os
import subprocess

import numpy as np
import pytest

from common.settings import Settings
from preprocess.features.moving import moving
from preprocess.features.signal_state import SIGNALS

BOARD_MOVING = os.path.join(os.path.dirname(__file__), "..", "board", "lib", "moving")
ROWS = 100_000


@pytest.fixture(scope="module")
def c_moving(tmp_path_factory):
    """Build board/lib/moving for this machine and give its `moving`."""
    folder = tmp_path_factory.mktemp("moving")
    (folder / "is_moving.c").write_text(
        '#include "moving.h"\n'
        "bool is_moving(const float *row, float min_speed)\n"
        "{\n\treturn moving(row, min_speed);\n}\n")
    library = folder / "moving.so"
    subprocess.run(["clang", "-shared", "-fPIC", "-Wall", "-Werror", "-I", BOARD_MOVING,
                    "-o", library, folder / "is_moving.c"], check=True)
    function = ctypes.CDLL(str(library)).is_moving
    function.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_float]
    function.restype = ctypes.c_bool
    return function


def test_the_c_port_matches_the_python(c_moving):
    """Rows around MIN_SPEED, as float32 like the board's. NaN fills 1% of cells."""
    rng = np.random.default_rng(0)
    min_speed = Settings().MIN_SPEED
    raw = rng.uniform(0.0, 2.0, (ROWS, len(SIGNALS))).astype(np.float32) * min_speed
    raw[rng.random(ROWS) < 0.02, SIGNALS.index("wheel_speed")] = min_speed
    raw[rng.random(raw.shape) < 0.01] = np.nan
    expected = moving(raw, min_speed=min_speed)
    row = ctypes.POINTER(ctypes.c_float)
    got = np.array([c_moving(raw[i].ctypes.data_as(row), min_speed) for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
