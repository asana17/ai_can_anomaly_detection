import random

import numpy as np

from attack.ramp import MOST, ramp
from preprocess.frames.spn_decode import decode
from preprocess.frames.spn_spec import SPEC

from can_frames import speed_frame

CCVS1_PGN = 65265
WHEEL = SPEC[CCVS1_PGN][0]


def _trace(seconds=60):
    """A minute of a truck speeding up and slowing down, so the speed has a spread."""
    return [speed_frame(i / 10, 50.0 + 20.0 * ((i // 100) % 2))
            for i in range(seconds * 10)]


def _speed(frame):
    return decode(frame.data, WHEEL.field)


def test_the_bias_grows_from_0_at_the_start_to_the_whole_at_the_stop():
    trace = _trace()
    hurt, info = ramp(trace, random.Random(0))
    assert info["pgn"] == CCVS1_PGN and info["signal"] == "wheel_speed"
    length = info["stop"] - info["start"]
    for before, after in zip(trace, hurt):
        if info["start"] <= before.timestamp <= info["stop"]:
            share = (before.timestamp - info["start"]) / length
            added = _speed(after) - _speed(before)
            assert abs(added - info["bias"] * share) <= WHEEL.field.scale


def test_the_bias_is_at_most_most_stds_of_the_signal():
    spread = np.std([_speed(f) for f in _trace()])
    for seed in range(20):
        _, info = ramp(_trace(), random.Random(seed))
        assert abs(info["bias"]) <= MOST * spread + 1e-9


def test_frames_outside_the_stretch_are_untouched():
    trace = _trace()
    hurt, info = ramp(trace, random.Random(1))
    for before, after in zip(trace, hurt):
        if not info["start"] <= before.timestamp <= info["stop"]:
            assert after == before


def test_times_and_count_survive():
    trace = _trace()
    hurt, _ = ramp(trace, random.Random(2))
    assert [f.timestamp for f in hurt] == [f.timestamp for f in trace]


def test_a_signal_that_never_moves_gives_nothing():
    flat = [speed_frame(i / 10, 50.0) for i in range(600)]
    assert ramp(flat, random.Random(0)) is None
