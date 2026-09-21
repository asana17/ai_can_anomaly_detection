import numpy as np

from evaluate.counting import detection
from common.settings import Settings


def _test_set(scores, hours=1.0):
    """A test set of `scores` rows, one attack on the first two, nothing else on."""
    n = len(scores)
    rows_to_score = {"rows": np.zeros((n, 17), dtype=np.float32),
                     "seg": np.zeros(n, dtype=int), "mv": np.ones(n, dtype=bool),
                     "quiet": np.arange(n) >= 2, "rules": np.zeros(n, dtype=bool),
                     "hours": hours}
    attacks_to_check = {"injected": [{"first": 0, "last": 1}],
                        "scorable": np.ones(1, dtype=bool)}
    return rows_to_score, attacks_to_check


def test_an_attack_is_found_when_a_row_of_it_is_flagged():
    flag = np.zeros(100, dtype=bool)
    flag[1] = True
    got = detection(flag, *_test_set(flag), Settings())
    assert [c["found"] for c in got] == [1, 0]      # one row cannot hold for ten


def test_a_model_that_flags_nothing_finds_nothing():
    flag = np.zeros(100, dtype=bool)
    got = detection(flag, *_test_set(flag), Settings())
    assert [c["found"] for c in got] == [0, 0]


def test_alarms_outside_an_attack_are_counted_by_the_hour():
    flag = np.zeros(100, dtype=bool)
    flag[50:60] = True
    got = detection(flag, *_test_set(flag, hours=2.0), Settings())
    assert [c["alarms_per_hour"] for c in got] == [0.5, 0.5]
