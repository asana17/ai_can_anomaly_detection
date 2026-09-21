import ctypes

import numpy as np
import pytest

from preprocess.features.signal_state import SIGNALS, SignalState
from preprocess.frames.spn_spec import SPEC

UPDATES = 100_000


@pytest.fixture(scope="module")
def c_state(board_lib):
    """Build board/lib/signal_state for this machine and give its functions."""
    library = board_lib(["signal_state", "spn_decode"],
                        '#include "signal_state.h"\n'
                        "size_t state_size(void)\n"
                        "{\n\treturn sizeof(SignalState);\n}\n"
                        "void clear(SignalState *state)\n"
                        "{\n\tsignal_state_clear(state);\n}\n"
                        "void update(SignalState *state, uint32_t pgn, const uint8_t *data,"
                        " size_t size)\n"
                        "{\n\tsignal_state_update(state, pgn, data, size);\n}\n"
                        "void row(const SignalState *state, float *out)\n"
                        "{\n\tsignal_state_row(state, out);\n}\n"
                        "bool ready(const SignalState *state)\n"
                        "{\n\treturn signal_state_ready(state);\n}\n"
                        "size_t slot(uint32_t pgn)\n"
                        "{\n\treturn signal_state_slot(pgn);\n}\n"
                        "size_t slot_count(void)\n"
                        "{\n\treturn SIGNAL_STATE_SLOTS;\n}\n")
    library.state_size.restype = ctypes.c_size_t
    library.update.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p,
                               ctypes.c_size_t]
    library.ready.restype = ctypes.c_bool
    library.slot.restype = ctypes.c_size_t
    library.slot_count.restype = ctypes.c_size_t
    return library


def test_updates_give_the_rows_and_readiness_of_the_python(c_state):
    """Payloads of 0 to 8 bytes with reserved values, and a PGN SPEC does not know."""
    rng = np.random.default_rng(0)
    pgns = list(SPEC) + [65408]
    state = ctypes.create_string_buffer(c_state.state_size())
    c_state.clear(state)
    python = SignalState()
    row = (ctypes.c_float * len(SIGNALS))()
    mismatched = []
    for i in range(UPDATES):
        pgn = pgns[rng.integers(len(pgns))]
        data = rng.choice([0x00, 0x42, 0xFE, 0xFF], 8, p=[0.25, 0.55, 0.1, 0.1])
        data = data[:rng.choice(9, p=[0.02] * 8 + [0.84])].astype(np.uint8).tobytes()
        c_state.update(state, pgn, data, len(data))
        python.update(pgn, data)
        c_state.row(state, row)
        expected = np.asarray(python.row(), np.float32)
        if (not np.array_equal(np.asarray(row), expected, equal_nan=True)
                or c_state.ready(state) != python.ready()):
            mismatched.append(i)
    assert python.ready()
    assert mismatched == []


def test_every_signal_of_a_pgn_reads_one_slot(c_state):
    slots = {pgn: c_state.slot(pgn) for pgn in SPEC}
    assert sorted(slots.values()) == sorted(set(slots.values()))
    assert all(at < c_state.slot_count() for at in slots.values())
    assert c_state.slot(65408) == c_state.slot_count(), "a PGN SPEC does not decode"
