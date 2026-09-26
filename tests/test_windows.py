import numpy as np

from preprocess.features.moving import moving
from preprocess.features.signal_state import SIGNALS
from preprocess.features.windows import positions, window_ends, window_rows
from rules.instant import range_check


def test_position_starts_again_at_a_stop_and_a_new_segment():
    moving = [True, True, False, True, True, True, True]
    segment = [0, 0, 0, 0, 0, 1, 1]
    assert positions(moving, segment).tolist() == [0, 1, -1, 0, 1, 0, 1]


def test_a_rule_hit_does_not_end_the_run():
    raw = np.zeros((5, len(SIGNALS)), np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = 50.0
    raw[2, SIGNALS.index("engine_speed")] = 9000.0    # above its J1939 range
    assert range_check.hits(raw).tolist() == [False, False, True, False, False]
    position = positions(moving(raw, min_speed=5.0), np.zeros(5, np.int32))
    assert position.tolist() == [0, 1, 2, 3, 4]


def test_no_window_before_rows_rows():
    position = positions([True] * 4 + [False] + [True] * 4, [0] * 9)
    assert window_ends(position, rows=5).tolist() == []


def test_a_window_every_row_at_stride_1():
    position = positions([True] * 8, [0] * 8)
    assert window_ends(position, rows=5).tolist() == [4, 5, 6, 7]


def test_a_window_every_stride_rows():
    position = positions([True] * 20, [0] * 20)
    assert window_ends(position, rows=5, stride=5).tolist() == [4, 9, 14, 19]


def test_the_ends_at_a_stride_are_some_of_the_ends_at_1():
    moving = np.tile([True] * 13 + [False], 5)
    segment = np.repeat(np.arange(7), 10)
    position = positions(moving, segment)
    every = set(window_ends(position, rows=5).tolist())
    for stride in (2, 3, 5):
        ends = window_ends(position, rows=5, stride=stride)
        assert len(ends) and set(ends.tolist()) <= every


def test_a_window_is_its_rows_oldest_first():
    grid_rows = np.arange(16, dtype=np.float32).reshape(8, 2)
    ends = window_ends(positions([True] * 8, [0] * 8), rows=3, stride=5)
    assert window_rows(grid_rows, ends, rows=3).tolist() == [
        [[0, 1], [2, 3], [4, 5]], [[10, 11], [12, 13], [14, 15]]]
