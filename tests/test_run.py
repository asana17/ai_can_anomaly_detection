import numpy as np

from evaluate.counting import alarms, found, period_of, persistent, touched
from evaluate.pc import run

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


def test_touched_says_which_attacks_have_a_flagged_row():
    flags = np.array([False, True, False, False, False, False])
    attacks = [{"first": 0, "last": 1}, {"first": 2, "last": 5}]
    assert touched(flags, attacks).tolist() == [True, False]


def test_seconds_for_measures_only_the_logs_it_lacks(tmp_path, monkeypatch):
    asked = []

    def fake(logs, min_speed):
        asked.append(list(logs))
        return {p: 1.0 for p in logs}

    monkeypatch.setattr(run, "seconds_above", fake)
    assert run.seconds_for(["a", "b"], str(tmp_path), run.Settings()) == {"a": 1.0, "b": 1.0}
    assert run.seconds_for(["b", "c"], str(tmp_path), run.Settings()) == {"b": 1.0, "c": 1.0}
    assert asked == [["a", "b"], ["c"]]


def test_grid_for_reads_the_logs_only_when_they_change(tmp_path, monkeypatch):
    asked = []

    def fake(logs):
        asked.append(list(logs))
        return (np.zeros((2, 3), np.float32), np.array([0.0, 0.1]),
                np.zeros(2, np.int32))

    monkeypatch.setattr(run, "grid_rows", fake)
    assert run.grid_for(["a"], str(tmp_path))[1] is False
    (raw, _, _), kept = run.grid_for(["a"], str(tmp_path))
    assert kept and raw.shape == (2, 3)
    run.grid_for(["a", "b"], str(tmp_path))
    assert asked == [["a"], ["a", "b"]]
