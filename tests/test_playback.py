import random

from attack.replay import playback
from preprocess.frames.can_log_loader import CanFrame
from preprocess.frames.spn_decode import decode
from preprocess.frames.spn_spec import SPEC

EEC1 = 0x18F004E6
EEC1_PGN = 61444
FIELDS = {spn.name: spn.field for spn in SPEC[EEC1_PGN]}


def _eec1(t, rpm, torque):
    rpm_raw, torque_raw = round(rpm / 0.125), round(torque + 125)
    return CanFrame(t, EEC1, bytes([0, torque_raw, torque_raw, rpm_raw & 0xFF,
                                    (rpm_raw >> 8) & 0xFF, 0, 0, 0]))


def _trace(seconds=60):
    """A minute of an engine speeding up while its torque swings."""
    return [_eec1(i / 10, 600 + i, (i % 50) - 25) for i in range(seconds * 10)]


def _value(frame, name):
    return decode(frame.data, FIELDS[name])


def test_one_signal_takes_the_values_it_had_from_the_source_on():
    trace = _trace()
    hurt, info = playback.replay(trace, random.Random(0))
    name = info["signal"]
    by_time = {round(f.timestamp, 1): f for f in trace}
    for before, after in zip(trace, hurt):
        if info["start"] <= before.timestamp <= info["stop"]:
            back = round(info["source"] + before.timestamp - info["start"], 1)
            near = [by_time.get(round(back + d, 1)) for d in (-0.1, 0.0, 0.1)]
            assert _value(after, name) in [_value(f, name) for f in near if f]


def test_the_other_signals_of_the_pgn_keep_their_values():
    trace = _trace()
    hurt, info = playback.replay(trace, random.Random(0))
    others = [n for n in FIELDS if n != info["signal"]]
    for before, after in zip(trace, hurt):
        for name in others:
            assert _value(after, name) == _value(before, name)


def test_frames_outside_the_stretch_are_untouched():
    trace = _trace()
    hurt, info = playback.replay(trace, random.Random(1))
    for before, after in zip(trace, hurt):
        if not info["start"] <= before.timestamp <= info["stop"]:
            assert after == before


def test_times_and_count_survive():
    trace = _trace()
    hurt, _ = playback.replay(trace, random.Random(2))
    assert [f.timestamp for f in hurt] == [f.timestamp for f in trace]


def test_the_stretch_and_the_source_lie_in_the_spans_given():
    _, info = playback.replay(_trace(), random.Random(0), spans=[(10.0, 22.0)])
    length = info["stop"] - info["start"]
    assert 10.0 <= info["start"] < info["stop"] <= 22.0
    assert 10.0 <= info["source"] <= 22.0 - length
