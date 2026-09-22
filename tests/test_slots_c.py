import ctypes
import math

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS, SignalState
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.spn_spec import SPEC

FRAMES = 20_000
OTHER_PGNS = (65262, 65263, 61440)


@pytest.fixture(scope="module")
def c_slots(board_lib):
    """Build board/lib/slots for this machine and give its functions."""
    library = board_lib(["slots", "can_id", "signal_state", "spn_decode"],
                        "#include <string.h>\n"
                        '#include "slots.h"\n'
                        "size_t slots_size(void)\n"
                        "{\n\treturn sizeof(Slots);\n}\n"
                        "void clear(Slots *slots)\n"
                        "{\n\tmemset(slots, 0, sizeof(*slots));\n}\n"
                        "void store(Slots *slots, uint32_t arb_id, const uint8_t *data,"
                        " size_t size, uint32_t time)\n"
                        "{\n\tslots_store(slots, arb_id, data, size, time);\n}\n"
                        "bool row(const Slots *slots, float *out)\n"
                        "{\n\tsignal_state_row(&slots->state, out);\n"
                        "\treturn signal_state_ready(&slots->state);\n}\n"
                        "uint32_t frames(const Slots *slots)\n"
                        "{\n\treturn slots->frames;\n}\n")
    library.slots_size.restype = ctypes.c_size_t
    library.clear.argtypes = [ctypes.c_void_p]
    library.store.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p,
                              ctypes.c_size_t, ctypes.c_uint32]
    library.row.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)]
    library.row.restype = ctypes.c_bool
    library.frames.argtypes = [ctypes.c_void_p]
    library.frames.restype = ctypes.c_uint32
    return library


def _frames(rng):
    """J1939 IDs of the PGNs the state decodes and a few it does not, with payloads."""
    pgns = [*SPEC, *OTHER_PGNS]
    for _ in range(FRAMES):
        pgn = pgns[rng.integers(len(pgns))]
        arb_id = (int(rng.integers(8)) << 26) | (pgn << 8) | int(rng.integers(256))
        yield arb_id, rng.integers(0, 256, int(rng.integers(0, 9)), np.uint8).tobytes()


def test_the_c_port_holds_what_the_pc_holds(c_slots):
    """After each frame the row read off the slots is the PC's, NaN for NaN."""
    slots = ctypes.create_string_buffer(c_slots.slots_size())
    c_slots.clear(slots)
    state = SignalState()
    got = (ctypes.c_float * len(SIGNALS))()
    for count, (arb_id, data) in enumerate(_frames(np.random.default_rng(0)), 1):
        c_slots.store(slots, arb_id, data, len(data), count)
        state.update(decompose_can_id(arb_id).pgn, data)
        assert c_slots.row(slots, got) == state.ready()
        expected = np.array(state.row(), np.float32)
        same = [a == b or (math.isnan(a) and math.isnan(b)) for a, b in zip(got, expected)]
        assert all(same), count
    assert c_slots.frames(slots) == FRAMES
