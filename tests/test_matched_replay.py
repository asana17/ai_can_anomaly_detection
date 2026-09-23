import random

import numpy as np

from attack.replay import matched_replay
from attack.replay.matched_replay import matched_sources
from preprocess.features.signal_state import SIGNALS
from preprocess.frames.can_log_loader import CanFrame

CCVS1, EEC1, TCO1 = 0x18FEF1E6, 0x18F004E6, 0x18FE6CE6


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


def _rows(speeds, gears, start=0.0, period=0.1):
    """A log's rows by time, holding a speed and a gear, as a grid holds them."""
    rows = {}
    for i, (kmh, gear) in enumerate(zip(speeds, gears)):
        row = np.full(len(SIGNALS), np.nan, np.float32)
        row[SIGNALS.index("wheel_speed")] = kmh
        row[SIGNALS.index("current_gear")] = gear
        rows[round(start + i * period, 3)] = row
    return rows


def _driving(speed=80.0, gear=10.0, seconds=60, start=0.0):
    """Rows of a truck holding one speed in one gear."""
    ticks = int(seconds * 10)
    return _rows([speed] * ticks, [gear] * ticks, start=start)


def test_only_the_donor_times_that_hold_the_speed_are_offered():
    mine = _driving(seconds=1)
    theirs = _rows([40.0] * 10 + [80.0] * 10, [10.0] * 20)
    offered = matched_sources(mine, theirs, 0.0, 0.9, period=0.1)
    assert offered == [1.0]


def test_a_donor_in_another_gear_is_not_offered():
    assert matched_sources(_driving(seconds=1), _rows([80.0] * 20, [9.0] * 20),
                           0.0, 0.9, period=0.1) == []


def test_a_donor_stretch_with_a_row_missing_is_not_offered():
    theirs = _driving(seconds=2)
    del theirs[0.5]
    offered = matched_sources(_driving(seconds=1), theirs, 0.0, 0.9, period=0.1)
    # every stretch reaching over the missing row is gone, the ones after it are left
    assert offered and min(offered) > 0.5


def test_the_source_walks_back_to_where_the_stretch_starts():
    # the stretch starts between two rows, so the source does too
    [offered] = matched_sources(_driving(seconds=1), _driving(seconds=1, start=5.0),
                                -0.05, 0.95, period=0.1)
    assert offered == 4.95


def _tacho(t, kmh):
    raw = round(kmh * 256)
    return CanFrame(t, TCO1, bytes([0, 0, 0, 0, 0, 0, raw & 0xFF, (raw >> 8) & 0xFF]))


def _tacho_log(kmh, seconds=60):
    return [_tacho(i / 10, kmh) for i in range(seconds * 10)]


def _donor(kmh, rows=None):
    """A donor, its rows by time and what loads its frames."""
    return (_driving() if rows is None else rows, lambda: _tacho_log(kmh))


def _matched(rng, donor_kmh):
    """A matched replay of the tachograph speed from a donor going `donor_kmh`."""
    return matched_replay.replay(_tacho_log(80.0), rng, [_donor(donor_kmh)],
                          rows=_driving(), period=0.1, pgns=(65132,))


def test_it_copies_from_a_matched_moment():
    hurt, info = _matched(random.Random(0), 80.5)
    assert info["pgn"] == 65132
    faked = [f.data for f in hurt if info["start"] <= f.timestamp <= info["stop"]]
    assert faked and all(d == _tacho(0.0, 80.5).data for d in faked)


def test_a_donor_that_matches_nowhere_gives_nothing():
    assert matched_replay.replay(_tacho_log(80.0), random.Random(0),
                          [_donor(80.5, _driving(speed=40.0))], rows=_driving(),
                          period=0.1, pgns=(65132,)) is None


def test_the_donor_drawn_is_one_that_matches():
    # only the second donor was driving this log's speed
    hurt, info = matched_replay.replay(_tacho_log(80.0), random.Random(0),
                                [_donor(60.5, _driving(speed=40.0)), _donor(80.5)],
                                rows=_driving(), period=0.1, pgns=(65132,))
    faked = [f.data for f in hurt if info["start"] <= f.timestamp <= info["stop"]]
    assert faked and all(d == _tacho(0.0, 80.5).data for d in faked)


def test_a_replay_the_change_limit_rule_catches_is_still_made():
    # 80 to 60 km/h between two frames is a jump no truck makes, and the injector
    # leaves saying so to whoever labels the attack
    hurt, info = _matched(random.Random(0), 60.0)
    assert info["pgn"] == 65132
    assert [f.data for f in hurt] != [f.data for f in _tacho_log(80.0)]


def test_one_seed_gives_one_matched_injection():
    a = _matched(random.Random(7), 80.5)[1]
    b = _matched(random.Random(7), 80.5)[1]
    assert a == b
