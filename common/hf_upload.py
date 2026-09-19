"""Upload a folder to Hugging Face, and print how to upload it again when that fails."""

from __future__ import annotations

from huggingface_hub import HfApi


def upload(repo, folder, message, repo_type="model", path_in_repo=None, revision=None,
           allow_patterns=None):
    """Upload `folder` to `repo` in one commit, and return that commit.

    When the upload fails, the `hf upload` command that does the same is printed before
    the error is raised again. The files stay in `folder`.
    """
    try:
        return HfApi().upload_folder(repo_id=repo, repo_type=repo_type,
                                     folder_path=folder, path_in_repo=path_in_repo,
                                     revision=revision, allow_patterns=allow_patterns,
                                     commit_message=message)
    except Exception:
        command = [f"hf upload {repo} {folder} {path_in_repo or '.'}",
                   f"--repo-type {repo_type}"]
        if revision:
            command.append(f"--revision {revision}")
        command += [f"--include '{p}'" for p in allow_patterns or []]
        command.append(f"--commit-message '{message}'")
        print(f"upload failed, {folder} is kept. To upload it again:\n"
              + " ".join(command), flush=True)
        raise
