import json

import numpy as np
import pytest

from assemble import split as split_stage
from assemble.split import split


def test_the_last_fold_tests_on_the_last_block():
    logs = [f"{i:03d}.csv" for i in range(100)]
    train, test = split({p: 1.0 for p in logs}, 4, 3)
    assert (train, test) == (logs[:75], logs[75:])


def test_the_first_fold_tests_on_the_first_block():
    logs = [f"{i:03d}.csv" for i in range(100)]
    train, test = split({p: 1.0 for p in logs}, 4, 0)
    assert (train, test) == (logs[25:], logs[:25])


def test_a_middle_fold_trains_on_both_sides():
    logs = [f"{i:03d}.csv" for i in range(100)]
    train, test = split({p: 1.0 for p in logs}, 4, 1)
    assert (train, test) == (logs[:25] + logs[50:], logs[25:50])


def test_a_fold_outside_the_blocks_is_refused():
    for fold in (-1, 4):
        with pytest.raises(ValueError):
            split({"a.csv": 1.0}, 4, fold)


def test_orders_by_filename_before_splitting():
    logs = ["c.csv", "a.csv", "b.csv"]  # not in order
    train, test = split({p: 1.0 for p in logs}, 3, 2)
    assert train + test == ["a.csv", "b.csv", "c.csv"]


def test_every_fold_covers_everything_once():
    logs = [f"{i:04d}.csv" for i in range(50)]
    for fold in range(4):
        train, test = split({p: 1.0 for p in logs}, 4, fold)
        assert sorted(train + test) == sorted(logs)


def test_the_seconds_size_the_parts_instead_of_the_log_count():
    logs = [f"{i:03d}.csv" for i in range(10)]
    seconds = {p: (100.0 if i < 2 else 0.0) for i, p in enumerate(logs)}
    seconds["009.csv"] = 100.0                    # the only moving traffic late on
    train, test = split(seconds, 3, 0)
    assert test == ["000.csv"]                    # a third of the moving traffic
    assert train == [f"{i:03d}.csv" for i in range(1, 10)]


def test_split_gives_test_nothing_when_no_log_holds_a_scoreable_second():
    logs = [f"{i:03d}.csv" for i in range(10)]
    train, test = split({p: 0.0 for p in logs}, 2, 1)
    assert (train, test) == (logs, [])


SECONDS = {f"part_1/{i:03d}.csv": 1.0 for i in range(8)}


def test_the_stage_writes_the_fold_s_logs(tmp_path, hub):
    hub.files = {"seconds/20260101-000000/seconds.json": SECONDS}
    made = split_stage.main("u/d", "abc", "seconds/20260101-000000", str(tmp_path))
    got = json.loads((tmp_path / made["path"] / "split.json").read_text())
    assert got["test"] == sorted(SECONDS)[6:]         # FOLD 3 of 4, the last quarter
    meta = json.loads((tmp_path / made["path"] / "meta.json").read_text())
    assert meta["seconds"] == {"repo": "u/d", "revision": "abc",
                               "path": "seconds/20260101-000000"}


def test_the_stage_names_a_split_of_the_same_seconds(tmp_path, hub):
    inputs = {"seconds": "seconds/20260101-000000", "n_splits": 4, "fold": 3}
    hub.files = {"splits/20260101-000000/meta.json": {"inputs": inputs}}
    found = split_stage.main("u/d", "abc", "seconds/20260101-000000", str(tmp_path))
    assert found["path"] == "splits/20260101-000000" and hub.uploaded == []
