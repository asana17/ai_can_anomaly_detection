"""Read from and add to a repository on Hugging Face, one directory at a time.

Each run, export and generation is one directory of the runs repository, and each base
and attack set one of the dataset repository. A directory is written into `runs_dir`
first and stays there, then uploaded in one commit, so a failed upload loses nothing.
"""

from __future__ import annotations

import os

from huggingface_hub import HfApi, snapshot_download

from common import hf_upload


def download(repo, path, runs_dir, repo_type="model"):
    """Directory `path` of `repo`, downloaded into `runs_dir`."""
    snapshot_download(repo, repo_type=repo_type, allow_patterns=[f"{path}/*"],
                      local_dir=runs_dir)
    return os.path.join(runs_dir, path)


def claim(repo, path, runs_dir, repo_type="model"):
    """Where in `runs_dir` to write directory `path`, checked before any work is done.

    It raises when the login fails, or when `path` is in `repo` or `runs_dir` already.
    """
    hub = HfApi()
    hub.whoami()                            # raises when not logged in
    if any(name.startswith(f"{path}/")
           for name in hub.list_repo_files(repo, repo_type=repo_type)):
        raise FileExistsError(f"{path} is in {repo} already")
    folder = os.path.join(runs_dir, path)
    if os.path.exists(folder):
        raise FileExistsError(f"{folder} is there already")
    return folder


def upload(repo, path, runs_dir, message, repo_type="model"):
    """Upload directory `path` of `runs_dir` to `repo` in one commit."""
    hf_upload.upload(repo, os.path.join(runs_dir, path), message, repo_type=repo_type,
                     path_in_repo=path)
