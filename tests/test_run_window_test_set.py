import numpy as np

from evaluate import run_window_test_set
from evaluate.run_test_set_common import AttackedRows, InjectedAttacks


def twenty_rows():
    """Twenty moving rows in one segment, one attack over rows 10 and 11, 18 rows of
    0.1 s with no attack."""
    rows = AttackedRows(normal_moving=np.ones(20, bool), rule_hit=np.zeros(20, bool),
                        segment=np.zeros(20, np.int32), hours=18 * 0.1 / 3600)
    attacks = InjectedAttacks(injected=[{"first": 10, "last": 11}],
                              worth_catching=np.array([True]))
    return rows, attacks


def score_on(*at):
    """A score of 1 on the rows `at`, 0 elsewhere."""
    scores = np.zeros(20)
    scores[list(at)] = 1.0
    return scores


def counted(scores, window_scores, n=3):
    """What the instant model caught with the window model, both at a threshold of
    0.5."""
    return run_window_test_set.detection_of_one_window_model(
        scores, 0.5, window_scores, 0.5, *twenty_rows(), n)


def test_the_window_model_adds_the_rows_it_is_judged_at():
    kept = counted(score_on(2), score_on(11, 16))
    assert list(kept) == ["1", "2", "3"]
    assert kept["1"]["caught"] == [0], "the window ending at row 11"
    assert kept["1"]["alarms_per_hour"] == 4000.0, \
        "rows 2 to 4 and row 16 are two alarms in 18 rows of 0.1 s"


def test_k_applies_to_the_instant_model_alone():
    kept = counted(score_on(2), score_on(11))
    assert kept["2"]["caught"] == [0], "the window model still alarms at row 11"
    assert kept["2"]["alarms_per_hour"] == 0.0, "row 2 alone is under 2 of 3"


def test_a_window_catches_an_attack_only_when_its_last_row_is_in_it():
    kept = counted(score_on(), score_on(13))    # the window holds rows 9 to 13
    assert kept["1"]["found"] == 0, \
        "it holds the attack's rows, but is judged after the attack ended"


def test_a_row_where_no_window_ends_does_not_alarm():
    window_scores = np.full(20, np.nan)
    assert counted(score_on(), window_scores)["1"]["found"] == 0


def test_each_window_model_is_counted_at_its_own_threshold():
    rows, attacks = twenty_rows()
    instant = [{"model": "nonlinear ae", "k": 8}, {"model": "nonlinear ae", "k": 4}]
    windows = [{"model": "var", "rows": 5}, {"model": "var", "rows": 10}]
    window_scores = np.stack([score_on(11), 1.5 * score_on(11)], axis=1)
    kept = run_window_test_set.detection_of_each_window_model(
        [{**instant[1], "threshold": 2.0}, {**instant[0], "threshold": 0.5}],
        instant, np.stack([score_on(10), score_on(10)], axis=1),
        [{**windows[1], "threshold": 2.0}, {**windows[0], "threshold": 0.5}],
        windows, window_scores, rows, attacks, 3)

    assert [(k["instant"]["k"], k["window"]["rows"]) for k in kept] == [
        (8, 5), (8, 10), (4, 5), (4, 10)]
    assert [(k["instant"]["threshold"], k["window"]["threshold"]) for k in kept] == [
        (0.5, 0.5), (0.5, 2.0), (2.0, 0.5), (2.0, 2.0)]
    assert [k["1"]["found"] for k in kept] == [1, 1, 1, 0], \
        "k 4 and the second window model are each under their own threshold"
