import json
import os

import pytest
import torch

from common import hf_upload, runs_repo
from evaluate.pc import record


class Hub:
    """Stands in for HfApi, logged in, with `files` in the repository."""

    files = ["results/20260101-000000/meta.json"]
    uploaded = []

    def whoami(self):
        return {"name": "test"}

    def list_repo_files(self, repo, repo_type="model"):
        return self.files

    def upload_folder(self, **kwargs):
        self.uploaded.append(kwargs)


def test_record_keeps_both_files_and_uploads_them(tmp_path, monkeypatch):
    monkeypatch.setattr(runs_repo, "HfApi", Hub)
    monkeypatch.setattr(hf_upload, "HfApi", Hub)
    Hub.uploaded = []
    run = record.start_run("user/runs", str(tmp_path))
    record.end_run(run, {"pca.k2.centre": torch.zeros(17)}, {"seeds": {"SEED": 0}})

    folder = tmp_path / "results" / run["stamp"]
    meta = json.loads((folder / "meta.json").read_text())
    assert sorted(os.listdir(folder)) == ["meta.json", "weights.safetensors"]
    assert meta["seeds"] == {"SEED": 0} and meta["commit"] == run["commit"]
    assert Hub.uploaded[0]["path_in_repo"] == f"results/{run['stamp']}"


def test_a_failed_upload_leaves_the_files(tmp_path, monkeypatch, capsys):
    class Failing(Hub):
        def upload_folder(self, **kwargs):
            raise ConnectionError("offline")

    monkeypatch.setattr(runs_repo, "HfApi", Failing)
    monkeypatch.setattr(hf_upload, "HfApi", Failing)
    run = record.start_run("user/runs", str(tmp_path))
    with pytest.raises(ConnectionError):
        record.end_run(run, {"pca.k2.centre": torch.zeros(17)}, {})
    assert (tmp_path / "results" / run["stamp"] / "weights.safetensors").exists()
    assert "hf upload user/runs" in capsys.readouterr().out


def test_claim_refuses_a_directory_the_repository_holds(tmp_path, monkeypatch):
    monkeypatch.setattr(runs_repo, "HfApi", Hub)
    monkeypatch.setattr(hf_upload, "HfApi", Hub)
    with pytest.raises(FileExistsError):
        runs_repo.claim("user/runs", "results/20260101-000000", str(tmp_path))
