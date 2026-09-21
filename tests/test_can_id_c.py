import ctypes

import numpy as np
import pytest

from preprocess.frames.can_id_decompose import decompose_can_id

IDS = 100_000


class CanId(ctypes.Structure):
    _fields_ = [("priority", ctypes.c_uint8), ("pgn", ctypes.c_uint32),
                ("source_address", ctypes.c_uint8)]


@pytest.fixture(scope="module")
def can_id_decompose(board_lib):
    """Build board/lib/can_id for this machine and give its `can_id_decompose`."""
    function = board_lib(["can_id"],
                         '#include "can_id.h"\n'
                         "CanId decompose(uint32_t arb_id)\n"
                         "{\n\treturn can_id_decompose(arb_id);\n}\n").decompose
    function.argtypes = [ctypes.c_uint32]
    function.restype = CanId
    return function


def test_the_c_port_matches_the_python(can_id_decompose):
    ids = np.random.default_rng(0).integers(0, 1 << 32, IDS, dtype=np.uint64).tolist()
    mismatched = []
    for arb_id in ids:
        got = can_id_decompose(arb_id)
        if (got.priority, got.pgn, got.source_address) != tuple(decompose_can_id(arb_id)):
            mismatched.append(arb_id)
    assert mismatched == []
