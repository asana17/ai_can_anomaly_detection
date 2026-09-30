import random

from attack.replay import all_pgn_replay
from can_frames import rpm_frame, speed_frame


def _trace(seconds=60):
    """A minute of a truck speeding up, its speed and engine speed each ten times a
    second."""
    return [frame for i in range(seconds * 10)
            for frame in (speed_frame(i / 10, 20 + i / 10), rpm_frame(i / 10 + 0.05,
                                                                     800 + i))]


def test_every_pgn_takes_the_payloads_it_had_from_the_same_source_on():
    trace = _trace()
    hurt, info = all_pgn_replay.replay(trace, random.Random(0))
    assert info["pgns"] == [61444, 65265]
    for before, after in zip(trace, hurt):
        if info["start"] <= before.timestamp <= info["stop"]:
            back = info["source"] + before.timestamp - info["start"]
            near = [f.data for f in trace
                    if f.can_id == before.can_id and abs(f.timestamp - back) <= 0.051]
            assert after.data in near


def test_frames_outside_the_stretch_are_untouched():
    trace = _trace()
    hurt, info = all_pgn_replay.replay(trace, random.Random(1))
    for before, after in zip(trace, hurt):
        if not info["start"] <= before.timestamp <= info["stop"]:
            assert after == before


def test_times_and_count_survive():
    trace = _trace()
    hurt, _ = all_pgn_replay.replay(trace, random.Random(2))
    assert [f.timestamp for f in hurt] == [f.timestamp for f in trace]


def test_a_log_with_none_of_the_pgns_is_left_alone():
    assert all_pgn_replay.replay(_trace(), random.Random(0), pgns=(61445,)) is None
