"""Read from and add to a repository on Hugging Face, one directory at a time.

Each run, export and generation is one directory of the runs repository, and each base
and attack set one of the dataset repository. A directory is written into `local_dir`
first and stays there, then uploaded in one commit, so a failed upload loses nothing.
"""

from __future__ import annotations

import json
import os
import time

from huggingface_hub import HfApi, hf_hub_download, snapshot_download

from common import hf_upload
from common.git import source


def download(repo, path, local_dir, repo_type="model", revision=None):
    """Directory `path` of `repo` at `revision`, downloaded into `local_dir`."""
    snapshot_download(repo, repo_type=repo_type, revision=revision,
                      allow_patterns=[f"{path}/*"], local_dir=local_dir)
    return os.path.join(local_dir, path)


def read_dir(repo, path, local_dir, revision, repo_type="model"):
    """Directory `path` of `repo` at `revision`, as its folder and its `meta.json`."""
    folder = download(repo, path, local_dir, repo_type=repo_type, revision=revision)
    with open(os.path.join(folder, "meta.json")) as f:
        return folder, json.load(f)


def find(repo, kind, inputs, local_dir, repo_type="model"):
    """The newest directory under `kind/` whose `meta.json` holds `inputs`, or None.

    It is returned as `{repo, revision, path}`, the revision being the one it was found
    at.
    """
    inputs = json.loads(json.dumps(inputs))     # a tuple comes back from meta.json a list
    revision = HfApi().repo_info(repo, repo_type=repo_type).sha
    for name in sorted(HfApi().list_repo_files(repo, repo_type=repo_type,
                                               revision=revision),
                       reverse=True):           # names are times, so newest first
        parts = name.split("/")
        if len(parts) != 3 or parts[0] != kind or parts[2] != "meta.json":
            continue
        meta = hf_hub_download(repo, name, repo_type=repo_type, revision=revision,
                               local_dir=local_dir)
        if json.load(open(meta))["inputs"] == inputs:
            return {"repo": repo, "revision": revision, "path": f"{kind}/{parts[1]}"}
    return None


def claim(repo, path, local_dir, repo_type="model"):
    """Where in `local_dir` to write directory `path`, checked before any work is done.

    It raises when the login fails, or when `path` is in `repo` or `local_dir` already.
    """
    hub = HfApi()
    hub.whoami()                            # raises when not logged in
    if any(name.startswith(f"{path}/")
           for name in hub.list_repo_files(repo, repo_type=repo_type)):
        raise FileExistsError(f"{path} is in {repo} already")
    folder = os.path.join(local_dir, path)
    if os.path.exists(folder):
        raise FileExistsError(f"{folder} is there already")
    return folder


def new_dir(repo, kind, local_dir, repo_type="model"):
    """Claim `kind/<now>/`, and return its path in `repo` and its folder in `local_dir`.

    The folder is made. It raises as `claim` does.
    """
    path = f"{kind}/{time.strftime('%Y%m%d-%H%M%S')}"
    folder = claim(repo, path, local_dir, repo_type)
    os.makedirs(folder)
    return path, folder


def upload(repo, path, local_dir, message, repo_type="model"):
    """Upload directory `path` of `local_dir` to `repo` in one commit.

    It prints and returns it as `{repo, revision, path}`, the revision being that commit.
    """
    commit = hf_upload.upload(repo, os.path.join(local_dir, path), message,
                              repo_type=repo_type, path_in_repo=path)
    print(f"{repo} {commit.oid} {path}", flush=True)
    return {"repo": repo, "revision": commit.oid, "path": path}


def write_meta(folder, meta, started, finished):
    """Write `meta` to `folder/meta.json`, with `started` and `finished` added.

    Both times are epoch seconds, written in local time.
    """
    stamp = "%Y-%m-%dT%H:%M:%S%z"
    with open(os.path.join(folder, "meta.json"), "w") as f:
        json.dump({**meta, "started": time.strftime(stamp, time.localtime(started)),
                   "finished": time.strftime(stamp, time.localtime(finished))},
                  f, indent=2)


def reuse_or_make(repo, kind, inputs, local_dir, write, rebuild=False,
                  repo_type="model"):
    """The directory under `kind/` made from `inputs`, as `{repo, revision, path}`.

    It is the one `repo` holds already, unless `rebuild`. Otherwise a new one is claimed,
    `write(folder)` writes its files and returns what to add to `meta.json`, and it is
    uploaded with `inputs` and the commit in `meta.json`.
    """
    found = find(repo, kind, inputs, local_dir, repo_type)
    if found and not rebuild:
        print(f"{found['path']} at {found['revision']} has the same inputs, pass it on "
              f"or run again with --rebuild", flush=True)
        return found
    started = time.time()
    path, folder = new_dir(repo, kind, local_dir, repo_type)
    code = source()
    meta = write(folder) or {}
    write_meta(folder, {"inputs": inputs, **meta, **code}, started, time.time())
    return upload(repo, path, local_dir, f"add {path} from {code['commit'][:7]}",
                  repo_type)
