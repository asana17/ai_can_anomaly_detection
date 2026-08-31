from attack.spoof import spoof
from preprocess.frames.can_log_loader import CanFrame
from preprocess.frames.frame_decode import decode_frame


def _ccvs1(t, raw):
    # CCVS1 (0x18FEF1E6); wheel_speed is bytes 1-2, little-endian
    return CanFrame(t, 0x18FEF1E6, bytes([0, raw & 0xFF, (raw >> 8) & 0xFF, 0, 0, 0, 0, 0]))


def test_spoof_changes_signal_only_in_window():
    frames = [_ccvs1(1.0, 25600), _ccvs1(5.0, 25600), _ccvs1(9.0, 25600)]  # 100 km/h
    out = spoof(frames, 65265, "wheel_speed", 5.0, 4.0, 6.0)
    speeds = [decode_frame(65265, f.data)["wheel_speed"] for f in out]
    assert speeds == [100.0, 5.0, 100.0]


def test_spoof_leaves_other_pgns_untouched():
    other = CanFrame(5.0, 0x18F004E6, bytes(8))  # EEC1, not CCVS1
    assert spoof([other], 65265, "wheel_speed", 5.0, 4.0, 6.0) == [other]
