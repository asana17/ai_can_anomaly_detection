import ctypes

import numpy as np
import pytest

from common.settings import TestRunSettings
from detect.alarm import alarmed_rows

ROWS = 100_000
THRESHOLD = 0.5


@pytest.fixture(scope="module")
def c_detect(board_lib):
    """Build board/lib/detect for this machine and give its functions."""
    library = board_lib(["detect"],
                        "#include <stddef.h>\n"
                        '#include "detect.h"\n'
                        "size_t detect_size(void)\n"
                        "{\n\treturn sizeof(DetectState);\n}\n"
                        "void clear(DetectState *state)\n"
                        "{\n\tdetect_clear(state);\n}\n"
                        "bool alarmed(DetectState *state, uint32_t number, float score,"
                        " float threshold, bool rule_hit, uint32_t hold)\n"
                        "{\n\treturn detect_alarmed(state, number, score, threshold,"
                        " rule_hit, hold);\n}\n")
    library.detect_size.restype = ctypes.c_size_t
    library.clear.argtypes = [ctypes.c_void_p]
    library.alarmed.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_float,
                                ctypes.c_float, ctypes.c_bool, ctypes.c_uint32]
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


@pytest.mark.parametrize("hold", (1, TestRunSettings().N))
def test_the_c_port_matches_the_python(c_detect, rows, hold):
    """Rows a gap apart restart the run, as a new segment does on the PC."""
    numbers, segment, scores, rule_hit = rows
    expected = alarmed_rows(scores, THRESHOLD, rule_hit, segment, hold, hold)
    state = ctypes.create_string_buffer(c_detect.detect_size())
    c_detect.clear(state)
    got = np.array([c_detect.alarmed(state, numbers[i], scores[i], THRESHOLD,
                                       bool(rule_hit[i]), hold) for i in range(ROWS)])
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []


def test_a_row_with_no_score_is_flagged_only_by_a_rule(c_detect):
    """NaN is never above the threshold, as on the PC."""
    state = ctypes.create_string_buffer(c_detect.detect_size())
    c_detect.clear(state)
    assert not c_detect.alarmed(state, 0, float("nan"), THRESHOLD, False, 1)
    assert c_detect.alarmed(state, 1, float("nan"), THRESHOLD, True, 1)
