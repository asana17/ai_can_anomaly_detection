import numpy as np

from evaluate.count_alarms import attacks_with_a_flagged_row, count_alarms


def test_alarms_count_stretches_not_rows():
    assert count_alarms(np.array([True, True, False, True, False, True, True,
                                  True])) == 3
    assert count_alarms(np.zeros(5, bool)) == 0
    assert count_alarms(np.ones(5, bool)) == 1


def test_which_attacks_have_a_flagged_row():
    flagged = np.array([False, True, False, False, False, False])
    attacks = [{"first": 0, "last": 1}, {"first": 2, "last": 5}]
    assert attacks_with_a_flagged_row(flagged, attacks).tolist() == [True, False]
