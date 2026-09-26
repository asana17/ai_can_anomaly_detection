import ctypes

import numpy as np
import pytest

from common.settings import TestRunSettings
from detect.alarm import alarmed_rows

ROWS = 100_000
THRESHOLD = 0.5


@pytest.fixture(scope="module")
def c_detect(board_lib):
    """Build detect_by_row.h for this machine and give its functions."""
    library = board_lib(["detect"],
                        "#include <stddef.h>\n"
                        '#include "detect_by_row.h"\n'
                        "uint32_t recent_flags(void)\n"
                        "{\n\treturn DETECT_BY_ROW_RECENT_FLAGS;\n}\n"
                        "size_t detect_size(void)\n"
                        "{\n\treturn sizeof(DetectByRow);\n}\n"
                        "void init(DetectByRow *state, float threshold,"
                        " uint32_t min_flagged_for_alarm)\n"
                        "{\n\tdetect_by_row_init(state, threshold, min_flagged_for_alarm);\n}\n"
                        "void push_flag(DetectByRow *state, uint32_t number,"
                        " float score, bool rule_hit)\n"
                        "{\n\tdetect_by_row_push_flag(state, number, score,"
                        " rule_hit);\n}\n"
                        "bool last_flagged(const DetectByRow *state)\n"
                        "{\n\treturn detect_by_row_last_flagged(state);\n}\n"
                        "bool alarmed(const DetectByRow *state)\n"
                        "{\n\treturn detect_by_row_alarmed(state);\n}\n")
    library.recent_flags.restype = ctypes.c_uint32
    library.detect_size.restype = ctypes.c_size_t
    library.init.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_uint32]
    library.push_flag.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_float,
                                  ctypes.c_bool]
    library.last_flagged.argtypes = [ctypes.c_void_p]
    library.last_flagged.restype = ctypes.c_bool
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
    assert c_detect.recent_flags() == TestRunSettings().N


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
        c_detect.push_flag(state, numbers[i], scores[i], bool(rule_hit[i]))
        flags.append(c_detect.last_flagged(state))
        alarms.append(c_detect.alarmed(state))
    assert expected.any() and not expected.all()
    assert np.array_equal(flags, (scores > THRESHOLD) | rule_hit)
    assert np.flatnonzero(np.array(alarms) != expected).tolist() == []


def test_a_row_with_no_score_is_flagged_only_by_a_rule(c_detect):
    """NaN is never above the threshold, as on the PC."""
    state = ctypes.create_string_buffer(c_detect.detect_size())
    c_detect.init(state, THRESHOLD, 1)
    c_detect.push_flag(state, 0, float("nan"), False)
    assert not c_detect.last_flagged(state)
    c_detect.push_flag(state, 1, float("nan"), True)
    assert c_detect.last_flagged(state)
