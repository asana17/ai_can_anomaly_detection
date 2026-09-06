from preprocess.features.grid_sample import resample
from preprocess.features.signal_state import SIGNALS
from preprocess.frames.can_log_loader import CanFrame


def _eec1(t, rpm):
    raw = round(rpm / 0.125)
    b = bytearray(8)
    b[3] = raw & 0xFF
    b[4] = (raw >> 8) & 0xFF
    return CanFrame(t, 0x18F004E6, bytes(b))


def _eec2(t):
    return CanFrame(t, 0x18F003E6, bytes(8))  # accel_pedal, engine_load = 0


def _ccvs1(t, kmh):
    raw = round(kmh / 0.00390625)
    return CanFrame(t, 0x18FEF1E6, bytes([0, raw & 0xFF, (raw >> 8) & 0xFF, 0, 0, 0, 0, 0]))


def _lfe1(t, lph):
    raw = round(lph / 0.05)
    return CanFrame(t, 0x18FEF2E6, bytes([raw & 0xFF, (raw >> 8) & 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]))


def _etc1(t, shaft=900.0):
    raw = round(shaft / 0.125)
    return CanFrame(t, 0x18F002E6, bytes([205, raw & 0xFF, (raw >> 8) & 0xFF, 0, 252,
                                          raw & 0xFF, (raw >> 8) & 0xFF, 255]))


def _etc2(t, gear=12):
    return CanFrame(t, 0x18F005E6, bytes([gear + 125, 0, 0, gear + 125, 0, 0, 0, 0]))


def _tco1(t, kmh=0.0):
    raw = round(kmh * 256)
    return CanFrame(t, 0x18FE6CE6, bytes([0, 0, 192, 192, 0, 0, raw & 0xFF, (raw >> 8) & 0xFF]))


def _ebc1(t, pedal=0.0):
    return CanFrame(t, 0x18F001E6, bytes([0xCF, round(pedal / 0.4), 0xCF, 255, 255, 255, 255, 255]))


def _vdc2(t):
    # steering, yaw and lateral hold mid range values, byte 8 is NA as on the truck
    return CanFrame(t, 0x18F009E6, bytes([0x7F, 0x7D, 0x60, 0x7F, 0x7D, 0x87, 0x7F, 0xFF]))


def _all_signals(t):
    return [_eec1(t, 800), _eec2(t), _ccvs1(t, 0.0), _lfe1(t, 2.0), _vdc2(t), _ebc1(t), _tco1(t), _etc1(t), _etc2(t)]


def test_emits_on_grid_holding_last_value():
    frames = _all_signals(0.0) + [_eec1(0.5, 1200), _eec1(2.3, 1500)]
    out = list(resample(frames, period=1.0, max_hold=5.0))
    assert [t for t, _ in out] == [1.0, 2.0]
    idx = SIGNALS.index("engine_speed")
    assert out[0][1][idx] == 1200.0  # held from t=0.5 at tick 1.0
    assert out[1][1][idx] == 1200.0  # 1500 arrives at 2.3, after tick 2.0


def test_no_emit_until_all_signals_seen():
    frames = [_eec1(0.0, 800), _eec1(2.0, 900)]  # only EEC1, never complete
    assert list(resample(frames, period=1.0, max_hold=5.0)) == []


def test_gap_is_skipped_not_filled():
    # without max_hold the 98 second gap becomes 98 rows of held values
    frames = (
        _all_signals(0.0) + _all_signals(1.0) + _all_signals(2.0)
        + _all_signals(100.0) + _all_signals(101.0)
    )
    out = list(resample(frames, period=1.0, max_hold=5.0))
    assert [t for t, _ in out] == [1.0, 2.0, 101.0]


def test_no_row_mixes_values_from_across_a_gap():
    # only EEC1 resumes, so a row here would pair a fresh rpm with a 100 s old speed
    frames = _all_signals(0.0) + [_eec1(t, 1500) for t in (100.0, 101.0, 102.0)]
    assert list(resample(frames, period=1.0, max_hold=5.0)) == []


def test_grid_restarts_from_the_frame_after_a_gap():
    frames = _all_signals(0.0) + _all_signals(100.4) + _all_signals(101.4)
    out = list(resample(frames, period=1.0, max_hold=5.0))
    assert [t for t, _ in out] == [101.4]   # not 101.0, which the old grid would give
