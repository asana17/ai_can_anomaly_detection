"""Read from and add to the runs repository on Hugging Face.

Each run, export and generation is one directory of the repository. It is written into
`runs_dir` first and stays there, then uploaded in one commit, so a failed upload loses
nothing.
"""

from __future__ import annotations

import os

from huggingface_hub import HfApi, snapshot_download


def download(repo, path, runs_dir):
    """Directory `path` of `repo`, downloaded into `runs_dir`."""
    snapshot_download(repo, allow_patterns=[f"{path}/*"], local_dir=runs_dir)
    return os.path.join(runs_dir, path)


def claim(repo, path, runs_dir):
    """Where in `runs_dir` to write directory `path`, checked before any work is done.

    It raises when the login fails, or when `path` is in `repo` or `runs_dir` already.
    """
    hub = HfApi()
    hub.whoami()                            # raises when not logged in
    if any(name.startswith(f"{path}/") for name in hub.list_repo_files(repo)):
        raise FileExistsError(f"{path} is in {repo} already")
    folder = os.path.join(runs_dir, path)
    if os.path.exists(folder):
        raise FileExistsError(f"{folder} is there already")
    return folder


def upload(repo, path, runs_dir, message):
    """Upload directory `path` of `runs_dir` to `repo` in one commit.

    When the upload fails, the files stay in `runs_dir`, and the command that uploads
    them later is printed before the error is raised again.
    """
    folder = os.path.join(runs_dir, path)
    try:
        HfApi().upload_folder(repo_id=repo, folder_path=folder, path_in_repo=path,
                              commit_message=message)
    except Exception:
        print(f"upload failed, {folder} is kept. To upload it later:\n"
              f"hf upload {repo} {folder} {path} --commit-message '{message}'",
              flush=True)
        raise
