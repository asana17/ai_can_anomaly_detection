"""
test_c_differential.py — Dual-Execution Differential Tests (Python vs C).

Runs test inputs through both the Python reference implementation and the
compiled C shared library (libpreprocess), asserting numerical and behavioral
equivalence.
"""
import pytest
import math

# Python implementations
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.spn_decode import decode as py_spn_decode, SpnField as PySpnField
from preprocess.frames.spn_spec import SPEC
from preprocess.features.signal_state import SignalState as PySignalState, SIGNALS
from preprocess.features.grid_sample import resample as py_resample
from preprocess.frames.can_log_loader import CanFrame

# C bindings
from preprocess_c.bindings import (
    c_can_id_decompose,
    c_spn_decode,
    CSignalState,
    c_resample,
)
from preprocess_c.compare.gen_golden import FRAMES

TOLERANCE = 1e-4

# ---------------------------------------------------------------------------
# 1. CAN ID Decomposition Differential Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("arb_id", [
    0x18F004E6,  # EEC1
    0x18F003E6,  # EEC2
    0x18FEF121,  # CCVS1
    0x18FE6CE6,  # TCO1
    0x18FEF2E6,  # LFE1
    0x18F002E6,  # ETC1
    0x18F005E6,  # ETC2
    0x18F001E6,  # EBC1
    0x18F009E6,  # VDC2
    0x0C000003,  # PDU1 format (PGN 0)
    0x18EAFF00,  # Request PGN
    0x98F004E6,  # Bit 31 flag set (should be masked)
    0xFFFFFFFF,  # All bits set
])
def test_diff_can_id_decompose(arb_id):
    py_res = decompose_can_id(arb_id)
    c_pri, c_pgn, c_sa = c_can_id_decompose(arb_id)

    assert py_res.priority == c_pri, f"Priority mismatch for {hex(arb_id)}"
    assert py_res.pgn == c_pgn, f"PGN mismatch for {hex(arb_id)}"
    assert py_res.source_address == c_sa, f"Source Address mismatch for {hex(arb_id)}"


# ---------------------------------------------------------------------------
# 2. SPN Decoding Differential Tests
# ---------------------------------------------------------------------------

def test_diff_spn_decode_all_specs():
    """Verify that every defined SPN decodes identically in Python and C."""
    # Test payloads: zeros, ones, alternating, known values
    payloads = [
        bytes([0x00] * 8),
        bytes([0x55] * 8),
        bytes([0xAA] * 8),
        bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0]),
        bytes([0x00, 0xAF, 0xB9, 0x80, 0x3E, 0x00, 0x00, 0x00]),
    ]

    for pgn, spns in SPEC.items():
        for spn in spns:
            f = spn.field
            py_f = PySpnField(f.start_bit, f.length, f.scale, f.offset)

            for data in payloads:
                py_val = py_spn_decode(data, py_f)
                c_val = c_spn_decode(data, f.start_bit, f.length, f.scale, f.offset)

                if py_val is None:
                    assert c_val is None, f"C should return None for SPN {spn.name}, data={data.hex()}"
                else:
                    assert c_val is not None, f"C returned None for SPN {spn.name}, data={data.hex()}"
                    assert abs(py_val - c_val) <= max(TOLERANCE, abs(py_val) * 1e-5), (
                        f"Mismatch for SPN {spn.name}: py={py_val}, c={c_val}"
                    )


def test_diff_spn_decode_unavailable_and_error():
    """Verify 0xFF (not available) and 0xFE (error) markers."""
    for pgn, spns in SPEC.items():
        for spn in spns:
            f = spn.field
            py_f = PySpnField(f.start_bit, f.length, f.scale, f.offset)

            # All 0xFF
            data_ff = bytes([0xFF] * 8)
            assert py_spn_decode(data_ff, py_f) is None
            assert c_spn_decode(data_ff, f.start_bit, f.length, f.scale, f.offset) is None

            # All 0xFE
            data_fe = bytes([0xFE] * 8)
            assert py_spn_decode(data_fe, py_f) is None
            assert c_spn_decode(data_fe, f.start_bit, f.length, f.scale, f.offset) is None


# ---------------------------------------------------------------------------
# 3. SignalState Differential Tests
# ---------------------------------------------------------------------------

def test_diff_signal_state_lifecycle():
    """Verify state initialization, partial updates, readiness, and row extraction."""
    py_s = PySignalState()
    c_s = CSignalState()

    assert py_s.ready() == c_s.ready() == False

    # Seed partial signals
    partial_1 = {"engine_speed": 1800.0, "wheel_speed": 85.0}
    py_s.update(partial_1)
    c_s.update(partial_1)
    assert py_s.ready() == c_s.ready() == False

    # Overwrite one signal, add more
    partial_2 = {"engine_speed": 1850.0, "fuel_rate": 22.5}
    py_s.update(partial_2)
    c_s.update(partial_2)
    assert py_s.ready() == c_s.ready() == False

    # Seed all remaining signals
    all_signals = {
        name: float(i * 10 + 1) for i, name in enumerate(SIGNALS)
    }
    py_s.update(all_signals)
    c_s.update(all_signals)

    assert py_s.ready() == c_s.ready() == True

    py_row = py_s.row()
    c_row = c_s.row()

    assert len(py_row) == len(c_row) == len(SIGNALS)
    for name, py_v, c_v in zip(SIGNALS, py_row, c_row):
        assert abs(py_v - c_v) <= TOLERANCE, f"Row mismatch on {name}: py={py_v}, c={c_v}"


# ---------------------------------------------------------------------------
# 4. Grid Sample Resampling Differential Tests
# ---------------------------------------------------------------------------

def test_diff_resample_golden_stream():
    """Verify full end-to-end resampling on the multi-PGN frame stream."""
    py_out = list(py_resample(FRAMES, period=0.1, max_hold=1.0))
    c_out = list(c_resample(FRAMES, period=0.1, max_hold=1.0))

    assert len(py_out) == len(c_out), f"Row count: Python={len(py_out)}, C={len(c_out)}"
    assert len(py_out) > 0, "Should emit at least one row"

    for (t_py, r_py), (t_c, r_c) in zip(py_out, c_out):
        assert abs(t_py - t_c) < 1e-4, f"Tick mismatch: py={t_py}, c={t_c}"
        for col_idx, (p_val, c_val) in enumerate(zip(r_py, r_c)):
            assert abs(p_val - c_val) <= TOLERANCE, (
                f"Row at {t_py:.3f} col {col_idx} ({SIGNALS[col_idx]}): "
                f"py={p_val}, c={c_val}"
            )


def test_diff_resample_gap_reset():
    """Verify that gaps exceeding max_hold reset both Python and C pipelines identically."""
    # Frames: seed at t=0, emit at t=0.1, gap of 2.0s (> 1.0s max_hold), re-seed at t=3.0, emit at t=3.1
    frames = list(FRAMES)

    # Add a gap by jumping 2.0 seconds forward:
    t_after_gap = 2.5
    # Add frames at t_after_gap for all signals
    for f in FRAMES[:9]:
        frames.append(CanFrame(t_after_gap, f.can_id, f.data))

    # Add trigger frames to produce tick at 2.6
    frames.append(CanFrame(t_after_gap + 0.1, 0x18F004E6, bytes([0x00, 0xAF, 0xB9, 0x80, 0x3E, 0, 0, 0])))

    py_out = list(py_resample(frames, period=0.1, max_hold=1.0))
    c_out = list(c_resample(frames, period=0.1, max_hold=1.0))

    assert len(py_out) == len(c_out)
    for (t_py, r_py), (t_c, r_c) in zip(py_out, c_out):
        assert abs(t_py - t_c) < 1e-4
        for col_idx, (p_val, c_val) in enumerate(zip(r_py, r_c)):
            assert abs(p_val - c_val) <= TOLERANCE
