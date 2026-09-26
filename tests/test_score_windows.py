import numpy as np

from scoring import score_windows

REVISION = "ab" * 20
SETS = ("calibration_set", "test_set", "log_split", "grid")
DATASET = {name: {"repo": "u/d", "revision": REVISION, "path": f"{name}s/20260101-000000"}
           for name in SETS}
ROWS = np.arange(4, dtype=np.float32)[:, None]
SEG = np.array([0, 0, 1, 1])


def sets_over(monkeypatch):
    """Fake a calibration set and a test set, both holding `ROWS`."""
    monkeypatch.setattr(score_windows, "fetch_calibration_set", lambda *args: {
        "calibration": ROWS, "seg": SEG, "min_speed": 5.0,
        "dataset": {name: DATASET[name]
                    for name in ("calibration_set", "log_split", "grid")}})
    monkeypatch.setattr(score_windows, "fetch_test_set", lambda *args: {
        "raw": ROWS, "seg": SEG, "min_speed": 5.0,
        "dataset": {name: DATASET[name] for name in ("test_set", "log_split", "grid")}})


def fetched(path, tmp_path):
    """What `fetch_set_rows` returns for the fake set at `path`."""
    return score_windows.fetch_set_rows(
        {"repo": "u/d", "revision": REVISION, "path": path}, str(tmp_path))


def test_a_calibration_set_gives_its_rows_and_their_segments(tmp_path, monkeypatch):
    sets_over(monkeypatch)
    rows, segments, min_speed, dataset = fetched("calibration_sets/20260101-000000",
                                                 tmp_path)

    assert np.array_equal(rows, ROWS) and np.array_equal(segments, SEG)
    assert min_speed == 5.0 and "calibration_set" in dataset


def test_a_test_set_gives_its_rows_and_their_segments(tmp_path, monkeypatch):
    sets_over(monkeypatch)
    rows, segments, min_speed, dataset = fetched("test_sets/20260101-000000", tmp_path)

    assert np.array_equal(rows, ROWS) and np.array_equal(segments, SEG)
    assert min_speed == 5.0 and "test_set" in dataset


class StandIn:
    """A stand-in window model of `rows` rows."""

    name = "stand-in"

    def __init__(self, rows):
        self.rows = rows


def test_a_window_scores_at_its_last_row_and_other_rows_get_nan():
    rows = np.arange(10, dtype=np.float32)[:, None]
    # row 4 is not moving, and row 8 starts a new segment
    moving = np.array([True] * 4 + [False] + [True] * 5)
    segments = np.array([0] * 8 + [1] * 2)
    got = {}

    def scorer_of(model):
        """Score a window by its last row's value, keeping the windows it was given."""
        def score(windows):
            got[model.rows] = windows
            return windows[:, -1, 0]
        return score

    scores, windows = score_windows.scores_of([StandIn(3), StandIn(2)], scorer_of,
                                              rows, moving, segments)

    assert got[3][:, :, 0].tolist() == [[0, 1, 2], [1, 2, 3], [5, 6, 7]], "oldest first"
    assert np.flatnonzero(~np.isnan(scores[:, 0])).tolist() == [2, 3, 7]
    assert scores[[2, 3, 7], 0].tolist() == [2, 3, 7]
    assert np.flatnonzero(~np.isnan(scores[:, 1])).tolist() == [1, 2, 3, 6, 7, 9]
    assert windows == [3, 6]
