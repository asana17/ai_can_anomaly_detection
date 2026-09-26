import ctypes

import numpy as np
import pytest

from common.settings import TestRunSettings
from detect.alarm import alarmed_rows

ROWS = 100_000
THRESHOLD = 0.5


@pytest.fixture(scope="module")
def c_detect(board_lib):
    """Build detect_instant.h for this machine and give its functions."""
    library = board_lib(["detect"],
                        "#include <stddef.h>\n"
                        '#include "detect_instant.h"\n'
                        "uint32_t rows(void)\n"
                        "{\n\treturn DETECT_INSTANT_ROWS;\n}\n"
                        "size_t detect_size(void)\n"
                        "{\n\treturn sizeof(DetectInstant);\n}\n"
                        "void init(DetectInstant *state, float threshold,"
                        " uint32_t k)\n"
                        "{\n\tdetect_instant_init(state, threshold, k);\n}\n"
                        "void add_row(DetectInstant *state, uint32_t number,"
                        " float score, bool rule_hit)\n"
                        "{\n\tdetect_instant_add_row(state, number, score,"
                        " rule_hit);\n}\n"
                        "bool last_row_flagged(const DetectInstant *state)\n"
                        "{\n\treturn detect_instant_last_row_flagged(state);\n}\n"
                        "bool alarmed(const DetectInstant *state)\n"
                        "{\n\treturn detect_instant_alarmed(state);\n}\n")
    library.rows.restype = ctypes.c_uint32
    library.detect_size.restype = ctypes.c_size_t
    library.init.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_uint32]
    library.add_row.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_float,
                                ctypes.c_bool]
    library.last_row_flagged.argtypes = [ctypes.c_void_p]
    library.last_row_flagged.restype = ctypes.c_bool
    library.alarmed.argtypes = [ctypes.c_void_p]
    library.alarmed.restype = ctypes.c_bool
    return library


@pytest.fixture(scope="module")
def rows():
    """Row numbers with gaps in them, scores around THRESHOLD and rule hits."""
    rng = np.random.default_rng(0)
    steps = np.where(rng.random(ROWS) < 0.02, rng.integers(2, 10, ROWS), 1)
    scores = rng.uniform(0.0, 2.0, ROWS).astype(np.float32) * THRESHOLD
    scores[rng.random(ROWS) < 0.01] = np.nan
    return (np.cumsum(steps, dtype=np.uint32), np.cumsum(steps != 1, dtype=np.int32),
            scores, rng.random(ROWS) < 0.02)


def test_the_c_rows_are_the_pc_n(c_detect):
    assert c_detect.rows() == TestRunSettings().N


@pytest.mark.parametrize("k", range(1, TestRunSettings().N + 1))
def test_the_c_port_matches_the_python(c_detect, rows, k):
    """A gap in the row numbers starts the count again, as a new segment does."""
    numbers, segment, scores, rule_hit = rows
    n = TestRunSettings().N
    expected = alarmed_rows(scores, THRESHOLD, rule_hit, segment, n, k)
    state = ctypes.create_string_buffer(c_detect.detect_size())
    c_detect.init(state, THRESHOLD, k)
    flags, alarms = [], []
    for i in range(ROWS):
        c_detect.add_row(state, numbers[i], scores[i], bool(rule_hit[i]))
        flags.append(c_detect.last_row_flagged(state))
        alarms.append(c_detect.alarmed(state))
    assert expected.any() and not expected.all()
    assert np.array_equal(flags, (scores > THRESHOLD) | rule_hit)
    assert np.flatnonzero(np.array(alarms) != expected).tolist() == []


def test_a_row_with_no_score_is_flagged_only_by_a_rule(c_detect):
    """NaN is never above the threshold, as on the PC."""
    state = ctypes.create_string_buffer(c_detect.detect_size())
    c_detect.init(state, THRESHOLD, 1)
    c_detect.add_row(state, 0, float("nan"), False)
    assert not c_detect.last_row_flagged(state)
    c_detect.add_row(state, 1, float("nan"), True)
    assert c_detect.last_row_flagged(state)
