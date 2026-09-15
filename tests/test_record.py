import json
import subprocess

import pytest
import torch

from evaluate.pc import record


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout


def _clone(tmp_path):
    """A clone of an empty bare repository, standing in for the runs repository."""
    remote, clone = tmp_path / "remote.git", tmp_path / "clone"
    _git("init", "-q", "--bare", "-b", "main", str(remote))
    _git("clone", "-q", str(remote), str(clone))
    _git("-C", str(clone), "config", "user.name", "test")
    _git("-C", str(clone), "config", "user.email", "test@example.com")
    _git("-C", str(clone), "commit", "-q", "--allow-empty", "-m", "init")
    _git("-C", str(clone), "push", "-q", "-u", "origin", "main")
    return remote, clone


def test_begin_refuses_a_directory_an_earlier_run_made(tmp_path, monkeypatch):
    monkeypatch.setattr(record.time, "time", lambda: 1_758_000_000.0)
    record.begin(str(tmp_path))
    with pytest.raises(FileExistsError):
        record.begin(str(tmp_path))


def test_record_writes_both_files_and_pushes_them(tmp_path):
    remote, clone = _clone(tmp_path)
    run = record.begin(str(clone))
    record.record(run, {"pca.k2.centre": torch.zeros(17)}, {"seeds": {"SEED": 0}})

    directory = clone / "results" / run["stamp"]
    meta = json.loads((directory / "meta.json").read_text())
    assert (directory / "weights.safetensors").exists()
    assert meta["seeds"] == {"SEED": 0} and meta["commit"] == run["commit"]
    pushed = _git("--git-dir", str(remote), "log", "--format=%s", "-1", "main")
    assert pushed.strip() == f"add {run['stamp']} from {run['commit'][:7]}"
