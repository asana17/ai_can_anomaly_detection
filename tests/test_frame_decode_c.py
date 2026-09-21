import ctypes

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS
from preprocess.frames.frame_decode import decode_frame
from preprocess.frames.spn_spec import SPEC

FRAMES = 100_000


class FrameDecodeValue(ctypes.Structure):
    _fields_ = [("signal", ctypes.c_size_t), ("value", ctypes.c_float)]


@pytest.fixture(scope="module")
def c_decode_frame(board_lib):
    """Build board/lib/spn_decode for this machine and give decode_frame's C port.

    It returns a {name: value} dict as the Python does.
    """
    function = board_lib("spn_decode",
                         '#include "frame_decode.h"\n'
                         "size_t decode(uint32_t pgn, const uint8_t *data, size_t size,"
                         " FrameDecodeValue *out)\n"
                         "{\n\treturn frame_decode(pgn, data, size, out);\n}\n", "decode")
    function.restype = ctypes.c_size_t
    out = (FrameDecodeValue * len(SIGNALS))()

    def decode(pgn, data):
        count = function(ctypes.c_uint32(pgn), bytes(data), ctypes.c_size_t(len(data)), out)
        return {SIGNALS[v.signal]: v.value for v in out[:count]}
    return decode


def test_every_raw_value_of_every_field_decodes_as_the_python(c_decode_frame):
    mismatched = []
    for pgn, defs in SPEC.items():
        for spn in defs:
            field = spn.field
            for raw in range(1 << field.length):
                data = (raw << field.start_bit).to_bytes(8, "little")
                if c_decode_frame(pgn, data) != decode_frame(pgn, data):
                    mismatched.append((spn.name, raw))
    assert mismatched == []


def test_random_frames_decode_as_the_python(c_decode_frame):
    """Payloads of 0 to 8 bytes, with the PGNs of SPEC and one it does not know."""
    rng = np.random.default_rng(0)
    pgns = list(SPEC) + [65408]
    mismatched = []
    for _ in range(FRAMES):
        pgn = pgns[rng.integers(len(pgns))]
        data = rng.integers(0, 256, rng.choice(9, p=[0.02] * 8 + [0.84]),
                            dtype=np.uint8).tobytes()
        if c_decode_frame(pgn, data) != decode_frame(pgn, data):
            mismatched.append((pgn, data.hex()))
    assert mismatched == []
