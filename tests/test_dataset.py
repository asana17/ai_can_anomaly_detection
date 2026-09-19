import numpy as np

from common import dataset
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
    assert dataset.grid_for(["a"], str(tmp_path))[1] is False
    (raw, _, _), kept = dataset.grid_for(["a"], str(tmp_path))
    assert kept and raw.shape == (2, 3)
    dataset.grid_for(["a", "b"], str(tmp_path))
    assert asked == [["a"], ["a", "b"]]
