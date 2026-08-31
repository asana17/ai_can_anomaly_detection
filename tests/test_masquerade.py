from attack.masquerade import masquerade
from preprocess.frames.can_log_loader import CanFrame
from preprocess.frames.frame_decode import decode_frame


def _ccvs1(t, raw):
    # CCVS1 (0x18FEF1E6); wheel_speed is bytes 1-2, little-endian
    return CanFrame(t, 0x18FEF1E6, bytes([0, raw & 0xFF, (raw >> 8) & 0xFF, 0, 0, 0, 0, 0]))


def _eec1(t):
    return CanFrame(t, 0x18F004E6, bytes(8))  # EEC1; engine_speed is bytes 4-5


def test_single_signal_overwrite_in_window():
    frames = [_ccvs1(1.0, 25600), _ccvs1(5.0, 25600), _ccvs1(9.0, 25600)]  # 100 km/h
    out = masquerade(frames, {65265: {"wheel_speed": 5.0}}, 4.0, 6.0)
    assert [decode_frame(65265, f.data)["wheel_speed"] for f in out] == [100.0, 5.0, 100.0]


def test_multi_signal_overwrite_across_pgns():
    frames = [_ccvs1(5.0, 25600), _eec1(5.0)]
    out = masquerade(
        frames,
        {65265: {"wheel_speed": 50.0}, 61444: {"engine_speed": 1500.0}},
        4.0,
        6.0,
    )
    assert decode_frame(65265, out[0].data)["wheel_speed"] == 50.0
    assert decode_frame(61444, out[1].data)["engine_speed"] == 1500.0


def test_timing_and_count_preserved():
    frames = [_ccvs1(1.0, 25600), _ccvs1(5.0, 25600)]
    out = masquerade(frames, {65265: {"wheel_speed": 5.0}}, 4.0, 6.0)
    assert [f.timestamp for f in out] == [1.0, 5.0]
    assert len(out) == len(frames)


def test_leaves_other_pgns_untouched():
    other = _eec1(5.0)
    assert masquerade([other], {65265: {"wheel_speed": 5.0}}, 4.0, 6.0) == [other]
