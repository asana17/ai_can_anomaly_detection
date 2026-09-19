import json

import numpy as np
import pytest

from assemble import dataset
from common.load_dataset import arrays_from, built_with
from common.settings import Settings


def test_seconds_for_measures_only_the_logs_it_lacks(tmp_path, monkeypatch):
    asked = []

    def fake(logs, min_speed):
        asked.append(list(logs))
        return {p: 1.0 for p in logs}

    monkeypatch.setattr(dataset, "seconds_above", fake)
    assert dataset.seconds_for(["a", "b"], str(tmp_path), Settings()) == {"a": 1.0, "b": 1.0}
    assert dataset.seconds_for(["b", "c"], str(tmp_path), Settings()) == {"b": 1.0, "c": 1.0}
    assert asked == [["a", "b"], ["c"]]


def test_grid_for_reads_the_logs_only_when_they_change(tmp_path, monkeypatch):
    asked = []

    def fake(logs):
        asked.append(list(logs))
        return (np.zeros((2, 3), np.float32), np.array([0.0, 0.1]),
                np.zeros(2, np.int32))

    monkeypatch.setattr(dataset, "grid_rows", fake)
    assert dataset.grid_for(["a"], str(tmp_path)) is False
    assert dataset.grid_for(["a"], str(tmp_path)) is True
    dataset.grid_for(["a", "b"], str(tmp_path))
    assert asked == [["a"], ["a", "b"]]


def built(tmp_path, settings):
    """Write the `built.json` an attack set on `settings` leaves."""
    with open(tmp_path / "built.json", "w") as f:
        json.dump({"logs": [["a"], ["b"]], **built_with(settings)}, f)


def test_seconds_for_measures_again_at_another_min_speed(tmp_path, monkeypatch):
    asked = []

    def fake(logs, min_speed):
        asked.append(min_speed)
        return {p: min_speed for p in logs}

    monkeypatch.setattr(dataset, "seconds_above", fake)
    dataset.seconds_for(["a"], str(tmp_path), Settings(MIN_SPEED=5.0))
    assert dataset.seconds_for(["a"], str(tmp_path), Settings(MIN_SPEED=8.0)) == {"a": 8.0}
    assert asked == [5.0, 8.0]


def test_arrays_from_refuses_a_dataset_built_otherwise(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset, "grid_rows", lambda logs: (
        np.zeros((2, 3), np.float32), np.array([0.0, 0.1]), np.zeros(2, np.int32)))
    dataset.grid_for(["a"], str(tmp_path))
    built(tmp_path, Settings(MIN_SPEED=5.0))
    with pytest.raises(ValueError):
        arrays_from(str(tmp_path), Settings(MIN_SPEED=8.0))


def test_arrays_from_puts_the_rows_on_the_saved_scale(tmp_path, monkeypatch):
    raw = np.array([[10.0, 1.0], [20.0, 3.0]], np.float32)
    monkeypatch.setattr(dataset, "grid_rows", lambda logs: (
        raw, np.array([0.0, 0.1]), np.zeros(2, np.int32)))
    monkeypatch.setattr("common.load_dataset.split_rows", lambda *args: (
        np.array([True, True]), np.array([False, False])))
    dataset.grid_for(["a"], str(tmp_path))
    built(tmp_path, Settings())
    np.save(tmp_path / "scale.npy", np.array([[10.0, 1.0], [2.0, 1.0]], np.float32))
    assert (arrays_from(str(tmp_path), Settings())["rows"] == [[0, 0], [5, 2]]).all()
