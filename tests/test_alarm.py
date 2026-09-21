import numpy as np

from detect.alarm import alarmed_rows, persistent

ONE = np.zeros(8, dtype=np.int32)          # one segment, so nothing breaks a run


def test_a_flag_counts_at_once_when_nothing_is_held():
    flag = np.array([False, True, False, True, True])
    assert np.array_equal(persistent(flag, ONE[:5], 1), flag)


def test_a_run_shorter_than_the_hold_never_counts():
    flag = np.array([True, True, False, True, True, True])
    assert not persistent(flag, ONE[:6], 3)[:3].any()
    assert persistent(flag, ONE[:6], 3)[5]


def test_the_hold_is_met_on_the_row_that_completes_it():
    flag = np.array([True] * 5)
    assert np.array_equal(persistent(flag, ONE[:5], 3),
                          np.array([False, False, True, True, True]))


def test_a_run_does_not_carry_across_a_segment():
    flag = np.array([True] * 6)
    segment = np.array([0, 0, 0, 1, 1, 1], dtype=np.int32)
    assert not persistent(flag, segment, 4).any(), "the break restarts the count"


def test_a_rule_hit_or_a_score_above_the_threshold_flags_a_row():
    scores = np.array([0.1, 0.9, np.nan, 0.2])
    rule_hit = np.array([False, False, True, False])
    assert alarmed_rows(scores, 0.5, rule_hit, ONE[:4], 1).tolist() == [
        False, True, True, False], "a row with no score is flagged only by a rule"
