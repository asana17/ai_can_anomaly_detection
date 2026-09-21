import numpy as np

from evaluate.counting import alarms, moved_by, period_of, touched


def test_alarms_counts_stretches_not_rows():
    assert alarms(np.array([True, True, False, True, False, True, True, True])) == 3
    assert alarms(np.zeros(5, bool)) == 0
    assert alarms(np.ones(5, bool)) == 1


def test_period_comes_from_the_commonest_step():
    times = np.array([0.0, 0.1, 0.2, 0.3, 30.0, 30.1])   # one recording gap
    assert abs(period_of(times) - 0.1) < 1e-9


def test_touched_says_which_attacks_have_a_flagged_row():
    flags = np.array([False, True, False, False, False, False])
    attacks = [{"first": 0, "last": 1}, {"first": 2, "last": 5}]
    assert touched(flags, attacks).tolist() == [True, False]


def test_an_attack_is_measured_by_the_largest_change_it_made():
    clean = {0.0: np.zeros(3, np.float32), 0.1: np.zeros(3, np.float32)}
    attacked = {"before": lambda log: clean,
                "raw": np.array([[1.0, 0.0, 0.0], [0.0, 3.0, 0.0]], np.float32),
                "t": np.array([0.0, 0.1]), "label": np.array([True, True])}

    moved = moved_by({"log": "a.csv", "first": 0, "last": 1}, attacked,
                           np.ones(3, np.float32))
    assert moved == 3.0, "the row it moved furthest is the one that counts"


def test_a_row_the_attack_left_alone_is_not_measured():
    clean = {0.0: np.zeros(2, np.float32), 0.1: np.zeros(2, np.float32)}
    attacked = {"before": lambda log: clean,
                "raw": np.array([[9.0, 0.0], [0.0, 2.0]], np.float32),
                "t": np.array([0.0, 0.1]), "label": np.array([False, True])}

    moved = moved_by({"log": "a.csv", "first": 0, "last": 1}, attacked,
                           np.ones(2, np.float32))
    assert moved == 2.0
