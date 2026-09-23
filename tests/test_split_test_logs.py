import json

import numpy as np
import pytest

from assemble import split_test_logs
from assemble.split_test_logs import split
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20


def test_the_last_fold_tests_on_the_last_part():
    logs = [f"{i:03d}.csv" for i in range(100)]
    non_test, test = split({p: 1.0 for p in logs}, 4, 3)
    assert (non_test, test) == (logs[:75], logs[75:])


def test_the_first_fold_tests_on_the_first_part():
    logs = [f"{i:03d}.csv" for i in range(100)]
    non_test, test = split({p: 1.0 for p in logs}, 4, 0)
    assert (non_test, test) == (logs[25:], logs[:25])


def test_a_middle_fold_leaves_non_test_on_both_sides():
    logs = [f"{i:03d}.csv" for i in range(100)]
    non_test, test = split({p: 1.0 for p in logs}, 4, 1)
    assert (non_test, test) == (logs[:25] + logs[50:], logs[25:50])


def test_a_fold_outside_the_parts_is_refused():
    for fold in (-1, 4):
        with pytest.raises(ValueError):
            split({"a.csv": 1.0}, 4, fold)


def test_orders_by_filename_before_splitting():
    logs = ["c.csv", "a.csv", "b.csv"]  # not in order
    non_test, test = split({p: 1.0 for p in logs}, 3, 2)
    assert non_test + test == ["a.csv", "b.csv", "c.csv"]


def test_every_fold_covers_everything_once():
    logs = [f"{i:04d}.csv" for i in range(50)]
    for fold in range(4):
        non_test, test = split({p: 1.0 for p in logs}, 4, fold)
        assert sorted(non_test + test) == sorted(logs)


def test_the_seconds_size_the_parts_instead_of_the_log_count():
    logs = [f"{i:03d}.csv" for i in range(10)]
    seconds = {p: (100.0 if i < 2 else 0.0) for i, p in enumerate(logs)}
    seconds["009.csv"] = 100.0                    # the only moving traffic late on
    non_test, test = split(seconds, 3, 0)
    assert test == ["000.csv"]                    # a third of the moving traffic
    assert non_test == [f"{i:03d}.csv" for i in range(1, 10)]


def test_split_gives_test_nothing_when_no_log_holds_a_scoreable_second():
    logs = [f"{i:03d}.csv" for i in range(10)]
    non_test, test = split({p: 0.0 for p in logs}, 2, 1)
    assert (non_test, test) == (logs, [])


LOGS = [f"part_1/{i:03d}.csv" for i in range(8)]


def _grid(hub, rows_per_log=10):
    """A grid of 8 logs, every row moving, `rows_per_log` rows each 100 ms apart."""
    raw = np.zeros((len(LOGS) * rows_per_log, len(SIGNALS)), np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = 50.0
    hub.files = {"grids/20260101-000000/logs.json": {"logs": LOGS,
                                                     "rows": [rows_per_log] * len(LOGS)},
                 "grids/20260101-000000/grid_raw.npy": raw,
                 "grids/20260101-000000/grid_t.npy": np.arange(len(raw)) * 0.1,
                 "grids/20260101-000000/meta.json": {"inputs": {"period": 0.1,
                                                                "max_hold": 1.0}}}
    return raw


def test_the_stage_writes_the_fold_s_logs_and_seconds(tmp_path, hub):
    _grid(hub)
    made = split_test_logs.main("u/d", REVISION, "grids/20260101-000000", str(tmp_path))
    got = json.loads((tmp_path / made["path"] / "log_split.json").read_text())
    assert got["test"] == LOGS[6:]                    # FOLD 3 of 4, the last quarter
    assert got["non_test"] == LOGS[:6]
    assert got["test_start"] == 6.0 and got["test_end"] == 7.9
    seconds = json.loads((tmp_path / made["path"] / "seconds.json").read_text())
    assert seconds == {log: 1.0 for log in LOGS}      # 10 moving rows, 100 ms apart
    meta = json.loads((tmp_path / made["path"] / "meta.json").read_text())
    assert meta["grid"] == {"repo": "u/d", "revision": REVISION,
                            "path": "grids/20260101-000000"}


def test_the_stage_counts_only_the_moving_rows(tmp_path, hub):
    raw = _grid(hub)
    raw[::2, SIGNALS.index("wheel_speed")] = 0.0      # the truck stops every other row
    made = split_test_logs.main("u/d", REVISION, "grids/20260101-000000", str(tmp_path))
    seconds = json.loads((tmp_path / made["path"] / "seconds.json").read_text())
    assert seconds == {log: 0.5 for log in LOGS}


def test_the_stage_names_a_log_split_of_the_same_grid(tmp_path, hub):
    inputs = {"grid": "grids/20260101-000000", "min_speed": 5.0, "n_splits": 4,
              "fold": 3}
    hub.files = {"log_splits/20260101-000000/meta.json": {"inputs": inputs}}
    found = split_test_logs.main("u/d", REVISION, "grids/20260101-000000",
                                 str(tmp_path))
    assert found["path"] == "log_splits/20260101-000000" and hub.uploaded == []
