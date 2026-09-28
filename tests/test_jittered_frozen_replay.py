import random

from attack.replay import frozen_replay, jittered_frozen_replay
from attack.replay.jittered_frozen_replay import jitter, steps
from preprocess.frames.spn_decode import extract_le
from preprocess.frames.spn_spec import SPEC

from can_frames import speed_frame

CCVS1_PGN = 65265
WHEEL = SPEC[CCVS1_PGN][0].field


def _raw(frame):
    return extract_le(frame.data, WHEEL.start_bit, WHEEL.length)


def _trace(seconds=60):
    """A minute of a truck accelerating by uneven steps."""
    return [speed_frame(i / 10, i / 10 + (i % 3) * 0.05) for i in range(seconds * 10)]


def test_the_steps_are_the_ones_the_log_took():
    trace = _trace()
    [taken] = steps(trace, CCVS1_PGN, [(0.0, 60.0)])
    assert taken == [_raw(b) - _raw(a) for a, b in zip(trace, trace[1:])]


def test_only_the_steps_within_the_spans_are_taken():
    [taken] = steps(_trace(), CCVS1_PGN, [(0.0, 0.25)])
    assert len(taken) == 2


def test_each_frame_is_the_held_value_plus_a_step_the_log_took():
    trace = _trace()
    held, info = frozen_replay.replay(trace, random.Random(0))
    hurt, same = jittered_frozen_replay.replay(trace, random.Random(0))
    assert same == info
    [taken] = steps(trace, CCVS1_PGN, [(0.0, 60.0)])
    for before, after in zip(held, hurt):
        if before != after:
            assert _raw(after) - _raw(before) in taken


def test_the_held_value_is_no_longer_held():
    hurt, info = jittered_frozen_replay.replay(_trace(), random.Random(0))
    faked = {f.data for f in hurt if info["start"] <= f.timestamp <= info["stop"]}
    assert len(faked) > 1


def test_frames_outside_the_stretch_are_untouched():
    trace = _trace()
    hurt, info = jittered_frozen_replay.replay(trace, random.Random(0))
    for before, after in zip(trace, hurt):
        if not info["start"] <= before.timestamp <= info["stop"]:
            assert after == before


def test_a_reserved_value_is_left_as_it_is():
    data = bytes([0, 0xFF, 0xFF, 0, 0, 0, 0, 0])
    for seed in range(10):
        assert jitter(data, CCVS1_PGN, [[-3, 5]], random.Random(seed)) == data


def test_a_step_below_zero_is_not_taken():
    data = speed_frame(0.0, 0.0).data
    for seed in range(10):
        assert _raw(speed_frame(0.0, 0.0)) <= extract_le(
            jitter(data, CCVS1_PGN, [[-1, 0, 1]], random.Random(seed)),
            WHEEL.start_bit, WHEEL.length)
