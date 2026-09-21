import pytest

from common.cli import arguments


def test_the_positional_names_come_back_in_order(monkeypatch):
    monkeypatch.setattr("sys.argv", ["stage", "u/d", "abc", "out"])
    assert arguments(("repo", "revision", "local_dir")) == ["u/d", "abc", "out"]


def test_a_false_flag_is_a_switch(monkeypatch):
    monkeypatch.setattr("sys.argv", ["stage", "out", "--rebuild"])
    assert arguments(("local_dir",), rebuild=False) == ["out", True]
    monkeypatch.setattr("sys.argv", ["stage", "out"])
    assert arguments(("local_dir",), rebuild=False) == ["out", False]


def test_any_other_flag_keeps_its_default(monkeypatch):
    monkeypatch.setattr("sys.argv", ["stage", "out"])
    assert arguments(("local_dir",), models="models.json") == ["out", "models.json"]
    monkeypatch.setattr("sys.argv", ["stage", "out", "--models", "mine.json"])
    assert arguments(("local_dir",), models="models.json") == ["out", "mine.json"]


def test_a_missing_positional_stops_the_stage(monkeypatch):
    monkeypatch.setattr("sys.argv", ["stage"])
    with pytest.raises(SystemExit):
        arguments(("local_dir",))
