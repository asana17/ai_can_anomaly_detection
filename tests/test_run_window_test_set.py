import numpy as np

from evaluate import run_window_test_set
from evaluate.run_test_set_common import AttackedRows, InjectedAttacks
from preprocess.features.windows import positions, window_ends


def twenty_rows():
    """Twenty moving rows in one segment, one attack over rows 10 and 11, 18 rows of
    0.1 s with no attack."""
    rows = AttackedRows(normal_moving=np.ones(20, bool), rule_hit=np.zeros(20, bool),
                        segment=np.zeros(20, np.int32), hours=18 * 0.1 / 3600)
    attacks = InjectedAttacks(injected=[{"first": 10, "last": 11}],
                              worth_catching=np.array([True]))
    return np.arange(20), rows, attacks


def counted(flag, window_scores, strides):
    """What the windows of 5 rows count, at a window threshold of 0.5."""
    position, rows, attacks = twenty_rows()
    return run_window_test_set.detection_with_one_window_model(
        flag, window_scores, 0.5, 5, position, rows, attacks, strides)


def flag_on_row_2_and_windows_on_11_and_16():
    flag = np.zeros(20, bool)
    flag[2] = True
    window_scores = np.full(20, np.nan)
    window_scores[4:] = 0.0
    window_scores[[11, 16]] = 1.0
    return flag, window_scores


def test_the_window_model_adds_the_windows_it_alarms():
    kept = counted(*flag_on_row_2_and_windows_on_11_and_16(), [1])
    assert [k["k"] for k in kept] == [1, 2, 3, 4, 5]
    first = kept[0]
    assert first["every_tick"]["found"] == 0
    assert first["every_tick"]["alarms_per_hour"] == 2000.0, \
        "windows ending at rows 4, 5 and 6 hold row 2, one alarm in 18 rows of 0.1 s"
    assert first["with_window_model"]["caught"] == [0], "the window ending at row 11"
    assert first["with_window_model"]["alarms_per_hour"] == 4000.0, \
        "the window ending at row 16 is one more alarm"


def test_k_counts_the_flagged_rows_of_a_window():
    kept = counted(*flag_on_row_2_and_windows_on_11_and_16(), [1])
    assert kept[1]["every_tick"]["alarms_per_hour"] == 0.0, "no window has 2 flags"


def test_a_stride_keeps_only_the_windows_ending_on_it():
    kept = counted(*flag_on_row_2_and_windows_on_11_and_16(), [5])
    assert kept[0]["with_window_model"]["found"] == 0, \
        "the windows end at rows 4, 9, 14 and 19, none of them at 11"


def test_a_window_catches_an_attack_only_when_its_last_row_is_in_it():
    window_scores = np.zeros(20)
    window_scores[13] = 1.0                 # the window holds rows 9 to 13
    kept = counted(np.zeros(20, bool), window_scores, [1])
    assert kept[0]["with_window_model"]["found"] == 0, \
        "it holds the attack's rows, but alarms after the attack ended"


def test_the_windows_at_a_stride_are_some_of_those_at_stride_one():
    rng = np.random.default_rng(4)
    position = positions(rng.random(500) < 0.9, np.cumsum(rng.random(500) < 0.02))
    for rows in (5, 10, 20):
        every = set(window_ends(position, rows=rows).tolist())
        for stride in (5, 10):
            at_stride = window_ends(position, rows=rows, stride=stride)
            assert set(at_stride.tolist()) <= every
