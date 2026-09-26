import numpy as np

from preprocess.features.windows import positions, window_ends

from evaluate.count_alarms import (attacks_with_a_flagged_row,
                                   count_false_positive_alarms,
                                   count_false_positive_window_alarms)


def test_which_attacks_have_a_flagged_row():
    flagged = np.array([False, True, False, False, False, False])
    attacks = [{"first": 0, "last": 1}, {"first": 2, "last": 5}]
    assert attacks_with_a_flagged_row(flagged, attacks).tolist() == [True, False]


def test_an_alarm_with_an_attacked_row_in_it_is_not_a_false_positive():
    alarmed = np.array([True, True, False, True, True, False, True])
    assert count_false_positive_alarms(alarmed, [{"first": 1, "last": 1}]) == 2
    assert count_false_positive_alarms(alarmed, []) == 3



def test_windows_at_stride_one_count_as_the_rows_they_end_on():
    rng = np.random.default_rng(2)
    moving = rng.random(400) < 0.9
    segment = np.cumsum(rng.random(400) < 0.02)
    position = positions(moving, segment)
    ends = window_ends(position, rows=5)
    alarmed = rng.random(len(ends)) < 0.3
    attacks = [{"first": 50, "last": 80}, {"first": 200, "last": 210}]
    rows = np.zeros(400, bool)
    rows[ends[alarmed]] = True
    assert count_false_positive_window_alarms(alarmed, ends, position, 1, attacks) == \
        count_false_positive_alarms(rows, attacks)


def test_windows_next_to_each_other_at_a_stride_are_one_alarm():
    position = np.arange(30)
    ends = window_ends(position, rows=5, stride=5)            # 4, 9, 14, 19, 24, 29
    alarmed = np.array([False, True, True, False, True, False])
    assert count_false_positive_window_alarms(alarmed, ends, position, 5, []) == 2


def test_a_window_alarm_does_not_carry_across_a_stop():
    moving = np.array([True] * 10 + [False] * 5 + [True] * 10)
    position = positions(moving, np.zeros(25, int))
    ends = window_ends(position, rows=5, stride=5)            # 4, 9, 19, 24
    assert ends.tolist() == [4, 9, 19, 24]
    alarmed = np.array([False, True, True, False])
    assert count_false_positive_window_alarms(alarmed, ends, position, 5, []) == 2, \
        "the windows either side of the stop are two alarms"


def test_a_window_alarm_that_ends_a_window_in_an_attack_is_not_a_false_positive():
    position = np.arange(30)
    ends = window_ends(position, rows=5, stride=5)
    alarmed = np.array([True, True, False, False, True, False])
    attacks = [{"first": 8, "last": 9}]
    assert count_false_positive_window_alarms(alarmed, ends, position, 5, attacks) == 1
