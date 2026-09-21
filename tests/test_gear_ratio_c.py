import ctypes
import os
import subprocess

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from rules.instant.gear_ratio import RATIOS, hits

SOURCE = os.path.join(os.path.dirname(__file__), "..", "board", "lib", "rules",
                      "gear_ratio.c")
GATE = 5.0
ROWS = 100_000


@pytest.fixture(scope="module")
def gear_ratio_hits(tmp_path_factory):
    """The C `gear_ratio_hits`, built for this machine."""
    library = tmp_path_factory.mktemp("gear_ratio") / "gear_ratio.so"
    subprocess.run(["clang", "-shared", "-fPIC", "-Wall", "-Werror", "-o", library,
                    SOURCE], check=True)
    function = ctypes.CDLL(str(library)).gear_ratio_hits
    function.argtypes = [ctypes.c_float] * 6
    function.restype = ctypes.c_bool
    return function


def _rows(rng):
    """Rows around each gate and gear boundary, as float32 like the board's."""
    gear = rng.choice([*RATIOS, 1, 3], ROWS).astype(np.float32)
    table = np.array([RATIOS.get(int(g), 100.0) for g in gear], dtype=np.float32)
    wheel = rng.uniform(0.0, 100.0, ROWS).astype(np.float32)
    engine = (wheel * table * rng.uniform(0.7, 1.3, ROWS)).astype(np.float32)
    engine[rng.random(ROWS) < 0.05] = 0.0
    selected = np.where(rng.random(ROWS) < 0.9, gear, gear + 1).astype(np.float32)
    slip = np.where(rng.random(ROWS) < 0.9, 0.0, 50.0).astype(np.float32)
    columns = {"engine_speed": engine, "wheel_speed": wheel, "current_gear": gear,
               "selected_gear": selected, "clutch_slip": slip}
    raw = np.zeros((ROWS, len(SIGNALS)), dtype=np.float32)
    for name, column in columns.items():
        raw[:, SIGNALS.index(name)] = column
    return raw


def test_the_c_port_matches_the_python_rule(gear_ratio_hits):
    raw = _rows(np.random.default_rng(0))
    expected = hits(raw, min_speed=GATE)
    columns = [raw[:, SIGNALS.index(name)] for name in
               ("engine_speed", "wheel_speed", "current_gear", "selected_gear",
                "clutch_slip")]
    got = np.array([gear_ratio_hits(*(float(c[i]) for c in columns), GATE)
                    for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
