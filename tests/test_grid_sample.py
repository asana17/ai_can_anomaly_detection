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


def _all_signals(t):
    return [_eec1(t, 800), _eec2(t), _ccvs1(t, 0.0), _lfe1(t, 2.0)]


def test_emits_on_grid_holding_last_value():
    frames = _all_signals(0.0) + [_eec1(0.5, 1200), _eec1(2.3, 1500)]
    out = list(resample(frames, period=1.0))
    assert [t for t, _ in out] == [1.0, 2.0]
    idx = SIGNALS.index("engine_speed")
    assert out[0][1][idx] == 1200.0  # held from t=0.5 at tick 1.0
    assert out[1][1][idx] == 1200.0  # 1500 arrives at 2.3, after tick 2.0


def test_no_emit_until_all_signals_seen():
    frames = [_eec1(0.0, 800), _eec1(2.0, 900)]  # only EEC1, never complete
    assert list(resample(frames, 1.0)) == []
