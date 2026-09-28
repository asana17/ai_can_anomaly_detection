import random

from attack.replay import repeated_replay
from preprocess.frames.can_log_loader import CanFrame

CCVS1 = 0x18FEF1E6


def _speed(t, kmh):
    raw = round(kmh / 0.00390625)
    return CanFrame(t, CCVS1, bytes([0, raw & 0xFF, (raw >> 8) & 0xFF, 0, 0, 0, 0, 0]))


def _trace(seconds=60):
    """A minute of a truck accelerating, so any two moments differ."""
    return [_speed(i / 10, i / 10) for i in range(seconds * 10)]


def _faked(hurt, info):
    return [f for f in hurt if info["start"] <= f.timestamp <= info["stop"]]


def test_the_stretch_before_the_start_is_sent_again_and_again():
    trace = _trace()
    hurt, info = repeated_replay.replay(trace, random.Random(0))
    assert info["source"] == info["start"] - 1.0 and info["repeat_seconds"] == 1.0
    before = {round(f.timestamp, 1): f.data for f in trace}
    for f in _faked(hurt, info):
        offset = (f.timestamp - info["start"]) % 1.0
        assert f.data in (before.get(round(info["source"] + offset, 1)),
                          before.get(round(info["source"] + offset + 0.1, 1)))


def test_the_stretch_before_the_start_lies_in_the_spans_given():
    _, info = repeated_replay.replay(_trace(), random.Random(0), spans=[(10.0, 22.0)])
    assert 10.0 <= info["source"] < info["stop"] <= 22.0


def test_a_span_with_no_room_before_gives_nothing():
    assert repeated_replay.replay(_trace(), random.Random(0), seconds=(2.0, 2.0),
                                  spans=[(10.0, 12.5)]) is None


def test_times_and_count_survive():
    trace = _trace()
    hurt, _ = repeated_replay.replay(trace, random.Random(2))
    assert [f.timestamp for f in hurt] == [f.timestamp for f in trace]
