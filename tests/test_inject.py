import random

from attack.inject import inject
from preprocess.frames.can_log_loader import CanFrame

CCVS1, EEC1 = 0x18FEF1E6, 0x18F004E6


def _speed(t, kmh):
    raw = round(kmh / 0.00390625)
    return CanFrame(t, CCVS1, bytes([0, raw & 0xFF, (raw >> 8) & 0xFF, 0, 0, 0, 0, 0]))


def _rpm(t, rpm):
    raw = round(rpm / 0.125)
    return CanFrame(t, EEC1, bytes([0, 0, 0, raw & 0xFF, (raw >> 8) & 0xFF, 0, 0, 0]))


def _trace(seconds=60):
    """A minute of a truck accelerating, so any two moments differ."""
    return [f for i in range(seconds * 10)
            for f in (_speed(i / 10, i / 10), _rpm(i / 10, 600 + i))]


def test_it_reports_what_it_faked():
    _, info = inject(_trace(), random.Random(0))
    assert info["pgn"] in (61444, 65265)
    assert info["stop"] > info["start"]
    assert 2.0 <= info["stop"] - info["start"] <= 10.0


def test_it_changes_bytes_only_inside_the_stretch():
    trace = _trace()
    hurt, info = inject(trace, random.Random(1))
    for before, after in zip(trace, hurt):
        if not info["start"] <= before.timestamp <= info["stop"]:
            assert after.data == before.data


def test_times_and_count_survive():
    trace = _trace()
    hurt, _ = inject(trace, random.Random(2))
    assert [f.timestamp for f in hurt] == [f.timestamp for f in trace]
    assert [f.can_id for f in hurt] == [f.can_id for f in trace]


def test_a_log_too_short_gives_nothing():
    assert inject(_trace(seconds=5), random.Random(0)) is None


def test_a_log_without_a_message_to_fake_gives_nothing():
    assert inject(_trace(), random.Random(0), messages=(65262,)) is None


def test_one_seed_gives_one_injection():
    a = inject(_trace(), random.Random(7))[1]
    b = inject(_trace(), random.Random(7))[1]
    assert a == b
