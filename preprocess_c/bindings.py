"""
bindings.py — Python ctypes bridge to the preprocess C shared library.

Allows Python tests and code to call into the compiled C implementation
directly, enabling automated differential testing against Python.
"""
from __future__ import annotations

import ctypes
import math
import os
import subprocess
import sys
from typing import Iterable, Iterator

_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_DIR, ".."))

# Locate shared library (dylib on macOS, so on Linux)
_LIB_NAME = "libpreprocess.dylib" if sys.platform == "darwin" else "libpreprocess.so"
_LIB_PATH = os.path.join(_DIR, _LIB_NAME)

if not os.path.exists(_LIB_PATH):
    # Auto-compile if not present
    subprocess.check_call(["make", "-C", _DIR])

_lib = ctypes.CDLL(_LIB_PATH)

NUM_SIGNALS = 17
NUM_PGNS = 9

# --- C Struct Definitions ---

class CanId(ctypes.Structure):
    _fields_ = [
        ("priority", ctypes.c_uint8),
        ("pgn", ctypes.c_uint32),
        ("source_address", ctypes.c_uint8),
    ]

class SpnField(ctypes.Structure):
    _fields_ = [
        ("start_bit", ctypes.c_uint8),
        ("length", ctypes.c_uint8),
        ("scale", ctypes.c_float),
        ("offset", ctypes.c_float),
    ]

class SpnDef(ctypes.Structure):
    _fields_ = [
        ("spn", ctypes.c_uint16),
        ("signal_index", ctypes.c_uint8),
        ("field", SpnField),
        ("minimum", ctypes.c_float),
        ("maximum", ctypes.c_float),
    ]

class PgnEntry(ctypes.Structure):
    _fields_ = [
        ("pgn", ctypes.c_uint32),
        ("defs", ctypes.POINTER(SpnDef)),
        ("count", ctypes.c_uint8),
    ]

class SignalState(ctypes.Structure):
    _fields_ = [
        ("values", ctypes.c_float * NUM_SIGNALS),
    ]

ROW_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32)

class GridSampler(ctypes.Structure):
    _fields_ = [
        ("state", SignalState),
        ("next_tick_ms", ctypes.c_uint32),
        ("prev_ms", ctypes.c_uint32),
        ("period_ms", ctypes.c_uint32),
        ("max_hold_ms", ctypes.c_uint32),
        ("on_row", ROW_CALLBACK),
        ("started", ctypes.c_bool),
    ]

# --- Function Prototypes ---

# CanId can_id_decompose(uint32_t arb_id)
_lib.can_id_decompose.argtypes = [ctypes.c_uint32]
_lib.can_id_decompose.restype = CanId

# float spn_decode(const uint8_t *data, uint8_t dlc, SpnField field)
_lib.spn_decode.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint8, SpnField]
_lib.spn_decode.restype = ctypes.c_float

# const PgnEntry *spn_spec_lookup(uint32_t pgn)
_lib.spn_spec_lookup.argtypes = [ctypes.c_uint32]
_lib.spn_spec_lookup.restype = ctypes.POINTER(PgnEntry)

# void signal_state_init(SignalState *s)
_lib.signal_state_init.argtypes = [ctypes.POINTER(SignalState)]
_lib.signal_state_init.restype = None

# void signal_state_update(SignalState *s, const float incoming[NUM_SIGNALS])
_lib.signal_state_update.argtypes = [ctypes.POINTER(SignalState), ctypes.POINTER(ctypes.c_float)]
_lib.signal_state_update.restype = None

# bool signal_state_ready(const SignalState *s)
_lib.signal_state_ready.argtypes = [ctypes.POINTER(SignalState)]
_lib.signal_state_ready.restype = ctypes.c_bool

# void signal_state_row(const SignalState *s, float row[NUM_SIGNALS])
_lib.signal_state_row.argtypes = [ctypes.POINTER(SignalState), ctypes.POINTER(ctypes.c_float)]
_lib.signal_state_row.restype = None

# void grid_sampler_init(GridSampler *g, uint32_t period_ms, uint32_t max_hold_ms, RowCallback on_row)
_lib.grid_sampler_init.argtypes = [ctypes.POINTER(GridSampler), ctypes.c_uint32, ctypes.c_uint32, ROW_CALLBACK]
_lib.grid_sampler_init.restype = None

# void grid_feed(GridSampler *g, uint32_t arb_id, const uint8_t *data, uint8_t dlc, uint32_t now_ms)
_lib.grid_feed.argtypes = [ctypes.POINTER(GridSampler), ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint8, ctypes.c_uint32]
_lib.grid_feed.restype = None

# --- Pythonic Helper Functions ---

def c_can_id_decompose(arb_id: int) -> tuple[int, int, int]:
    """Decompose raw CAN ID using C implementation -> (priority, pgn, source_address)."""
    res = _lib.can_id_decompose(ctypes.c_uint32(arb_id))
    return (res.priority, res.pgn, res.source_address)

def c_spn_decode(data: bytes, start_bit: int, length: int, scale: float, offset: float) -> float | None:
    """Decode single SPN using C implementation -> float physical value or None."""
    field = SpnField(start_bit=start_bit, length=length, scale=scale, offset=offset)
    c_buf = (ctypes.c_uint8 * len(data))(*data)
    val = _lib.spn_decode(c_buf, len(data), field)
    if math.isnan(val):
        return None
    return float(val)

class CSignalState:
    """Pythonic wrapper around C SignalState struct."""
    def __init__(self):
        self._state = SignalState()
        _lib.signal_state_init(ctypes.byref(self._state))

    def update(self, values: dict[str, float]) -> None:
        """Update using a name->value dict matching Python SignalState.update()."""
        from preprocess.features.signal_state import SIGNALS
        incoming = (ctypes.c_float * NUM_SIGNALS)()
        for i in range(NUM_SIGNALS):
            incoming[i] = float('nan')

        for name, v in values.items():
            if name in SIGNALS:
                idx = SIGNALS.index(name)
                incoming[idx] = float(v)

        _lib.signal_state_update(ctypes.byref(self._state), incoming)

    def ready(self) -> bool:
        return bool(_lib.signal_state_ready(ctypes.byref(self._state)))

    def row(self) -> list[float]:
        out = (ctypes.c_float * NUM_SIGNALS)()
        _lib.signal_state_row(ctypes.byref(self._state), out)
        return [float(x) for x in out]

def c_resample(
    frames: Iterable,
    period: float = 0.1,
    max_hold: float = 1.0,
) -> Iterator[tuple[float, list[float]]]:
    """
    Run frames through C GridSampler and yield (tick_timestamp, row) tuples,
    matching the Python preprocess.features.grid_sample.resample() generator.
    """
    period_ms = int(round(period * 1000.0))
    max_hold_ms = int(round(max_hold * 1000.0))

    collected: list[tuple[float, list[float]]] = []

    def on_row_cb(row_ptr, tick_ms):
        row = [float(row_ptr[i]) for i in range(NUM_SIGNALS)]
        collected.append((tick_ms / 1000.0, row))

    cb_func = ROW_CALLBACK(on_row_cb)

    sampler = GridSampler()
    _lib.grid_sampler_init(ctypes.byref(sampler), period_ms, max_hold_ms, cb_func)

    # Reference timestamp for offset conversion if float timestamps are in seconds
    t0 = None
    for f in frames:
        if t0 is None:
            t0 = f.timestamp
        # Timestamp in ms relative to first frame to avoid large uint32 numbers
        # or absolute ms
        now_ms = int(round(f.timestamp * 1000.0))
        c_buf = (ctypes.c_uint8 * len(f.data))(*f.data)
        _lib.grid_feed(ctypes.byref(sampler), f.can_id, c_buf, len(f.data), now_ms)
        while collected:
            yield collected.pop(0)
