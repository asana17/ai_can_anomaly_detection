import numpy as np

from detect.alarm import alarmed_rows, k_of_last_n

ONE = np.zeros(8, dtype=np.int32)          # one segment, so nothing breaks a run


def rows_in_a_row(flag, segment, need):
    """True where `need` rows in a row are flagged, the alarm before k of the last n."""
    out, run = np.zeros(len(flag), bool), 0
    for i in range(len(flag)):
        run = run + 1 if flag[i] and i and segment[i] == segment[i - 1] else int(flag[i])
        out[i] = run >= need
    return out


def test_k_equal_to_n_is_the_same_as_rows_in_a_row():
    rng = np.random.default_rng(0)
    flag = rng.random(500) < 0.6
    segment = np.cumsum(rng.random(500) < 0.05)
    for n in (1, 2, 5, 10):
        assert np.array_equal(k_of_last_n(flag, segment, n, n),
                              rows_in_a_row(flag, segment, n)), n


def test_one_of_n_is_the_flag_at_n_one():
    flag = np.array([False, True, False, True, True])
    assert np.array_equal(k_of_last_n(flag, ONE[:5], 1, 1), flag)


def test_a_count_does_not_carry_across_a_segment():
    flag = np.array([True] * 6)
    segment = np.array([0, 0, 0, 1, 1, 1], dtype=np.int32)
    assert not k_of_last_n(flag, segment, 6, 4).any(), "the break restarts the count"


def test_a_row_missing_from_a_stretch_still_alarms_on_k():
    flag = np.array([True, True, False, True, True, False])
    assert k_of_last_n(flag, ONE[:6], 5, 4).tolist() == [
        False, False, False, False, True, False]


def test_the_start_of_a_segment_counts_the_rows_it_has():
    flag = np.array([True, True, True, False, False])
    assert k_of_last_n(flag, ONE[:5], 10, 3).tolist() == [
        False, False, True, True, True]


def test_a_rule_hit_or_a_score_above_the_threshold_flags_a_row():
    scores = np.array([0.1, 0.9, np.nan, 0.2])
    rule_hit = np.array([False, False, True, False])
    assert alarmed_rows(scores, 0.5, rule_hit, ONE[:4], 1, 1).tolist() == [
        False, True, True, False], "a row with no score is flagged only by a rule"
