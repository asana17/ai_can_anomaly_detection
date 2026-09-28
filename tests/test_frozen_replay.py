import random

from attack.replay import frozen_replay
from preprocess.frames.can_log_loader import CanFrame

CCVS1 = 0x18FEF1E6


def _speed(t, kmh):
    raw = round(kmh / 0.00390625)
    return CanFrame(t, CCVS1, bytes([0, raw & 0xFF, (raw >> 8) & 0xFF, 0, 0, 0, 0, 0]))


def _trace(seconds=60):
    """A minute of a truck accelerating, so any two moments differ."""
    return [_speed(i / 10, i / 10) for i in range(seconds * 10)]


def test_it_holds_the_payload_of_the_start():
    trace = _trace()
    hurt, info = frozen_replay.replay(trace, random.Random(0))
    assert info["source"] == info["start"] and info["repeat_seconds"] == 0.0
    assert len({f.data for f in hurt
                if info["start"] <= f.timestamp <= info["stop"]}) == 1


def test_times_and_count_survive():
    trace = _trace()
    hurt, _ = frozen_replay.replay(trace, random.Random(2))
    assert [f.timestamp for f in hurt] == [f.timestamp for f in trace]


def test_a_log_that_does_not_change_gives_nothing():
    flat = [_speed(i / 10, 50.0) for i in range(600)]
    assert frozen_replay.replay(flat, random.Random(0)) is None
