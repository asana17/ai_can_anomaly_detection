import fnmatch
import json
import os

import pytest

from common import hf_upload, hub_dirs


@pytest.fixture
def hub(monkeypatch):
    """Stands in for a Hugging Face repository, logged in.

    `hub.files` maps a path in the repository to the JSON it holds. Uploads are kept in
    `hub.uploaded`.
    """
    class Hub:
        files = {}
        uploaded = []

        def whoami(self):
            return {"name": "test"}

        def repo_info(self, repo, repo_type="model"):
            return type("Info", (), {"sha": "abc"})

        def list_repo_files(self, repo, repo_type="model", revision=None):
            return list(Hub.files)

        def upload_folder(self, **kwargs):
            Hub.uploaded.append(kwargs)
            return type("Commit", (), {"oid": "def"})

    def fetch(name, local_dir):
        path = os.path.join(local_dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(Hub.files[name], f)
        return path

    def hf_hub_download(repo, name, repo_type, revision, local_dir):
        return fetch(name, local_dir)

    def snapshot_download(repo, repo_type, allow_patterns, local_dir, revision=None):
        for name in Hub.files:
            if any(fnmatch.fnmatch(name, p) for p in allow_patterns):
                fetch(name, local_dir)

    monkeypatch.setattr(hub_dirs, "HfApi", Hub)
    monkeypatch.setattr(hf_upload, "HfApi", Hub)
    monkeypatch.setattr(hub_dirs, "hf_hub_download", hf_hub_download)
    monkeypatch.setattr(hub_dirs, "snapshot_download", snapshot_download)
    return Hub
