import math

from preprocess.features.signal_state import SIGNALS, SignalState

EEC1 = 61444
ENGINE_SPEED_1000 = bytes([0, 0, 0, 0x40, 0x1F, 0, 0, 0])   # raw 8000 * 0.125


def test_row_decodes_the_latest_payload():
    s = SignalState()
    s.update(EEC1, bytes(8))
    s.update(EEC1, ENGINE_SPEED_1000)
    assert s.row()[SIGNALS.index("engine_speed")] == 1000.0


def test_a_reserved_value_is_nan_not_the_one_before():
    s = SignalState()
    s.update(EEC1, ENGINE_SPEED_1000)
    s.update(EEC1, bytes([0, 0, 0, 0xFF, 0xFF, 0, 0, 0]))
    assert math.isnan(s.row()[SIGNALS.index("engine_speed")])


def test_a_pgn_not_in_spec_is_ignored():
    s = SignalState()
    s.update(65408, bytes(8))
    assert all(math.isnan(v) for v in s.row())


def test_ready_once_every_pgn_has_arrived():
    s = SignalState()
    assert not s.ready()
    for pgn in (61444, 61443, 65265, 65266, 61442, 61445, 65132, 61441):
        s.update(pgn, bytes(8))
    assert not s.ready()
    s.update(61449, bytes([0xFF] * 8))
    assert s.ready(), "a PGN whose values are all reserved has still arrived"


def test_signals_come_from_spec():
    assert "engine_speed" in SIGNALS
    assert "wheel_speed" in SIGNALS
    assert "yaw_rate" in SIGNALS
    assert len(SIGNALS) == 17
