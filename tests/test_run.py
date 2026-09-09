import numpy as np

from evaluate.run import alarms, found, period_of, persistent

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


def test_alarms_counts_stretches_not_rows():
    assert alarms(np.array([True, True, False, True, False, True, True, True])) == 3
    assert alarms(np.zeros(5, bool)) == 0
    assert alarms(np.ones(5, bool)) == 1


def test_period_comes_from_the_commonest_step():
    times = np.array([0.0, 0.1, 0.2, 0.3, 30.0, 30.1])   # one recording gap
    assert abs(period_of(times) - 0.1) < 1e-9


def test_found_counts_an_attack_once_however_many_rows_it_flags():
    flags = np.array([False, True, True, False, False, False])
    attacks = [{"first": 1, "last": 2}, {"first": 3, "last": 5}]
    assert found(flags, attacks, np.array([True, True])) == 1
    assert found(flags, attacks, np.array([False, True])) == 0
