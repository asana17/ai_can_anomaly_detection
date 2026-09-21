import ctypes
import os
import subprocess

import numpy as np
import pytest

from preprocess.frames.can_id_decompose import decompose_can_id

BOARD_CAN_ID = os.path.join(os.path.dirname(__file__), "..", "board", "lib", "can_id")
IDS = 100_000


class CanId(ctypes.Structure):
    _fields_ = [("priority", ctypes.c_uint8), ("pgn", ctypes.c_uint32),
                ("source_address", ctypes.c_uint8)]


@pytest.fixture(scope="module")
def can_id_decompose(tmp_path_factory):
    """Build board/lib/can_id for this machine and give its `can_id_decompose`."""
    folder = tmp_path_factory.mktemp("can_id")
    (folder / "decompose.c").write_text(
        '#include "can_id.h"\n'
        "CanId decompose(uint32_t arb_id)\n"
        "{\n\treturn can_id_decompose(arb_id);\n}\n")
    library = folder / "can_id.so"
    subprocess.run(["clang", "-shared", "-fPIC", "-Wall", "-Werror", "-I", BOARD_CAN_ID,
                    "-o", library, folder / "decompose.c"], check=True)
    function = ctypes.CDLL(str(library)).decompose
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
