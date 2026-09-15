"""Keep each run of the comparison in the runs repository.

A run's weights and numbers are worth keeping, but `out` is only a cache. So each run
gets its own directory in a clone of it, committed and pushed there.
`begin` claims the directory when the run starts, and `record` fills it at the end.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time

import numpy as np
import torch
from safetensors.torch import save_file


def git(*args):
    """What a git command prints."""
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout


def begin(runs_repo):
    """Claim `results/<start time>/` in `runs_repo`, and note the code it starts from."""
    started = time.time()
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(started))
    os.makedirs(os.path.join(runs_repo, "results", stamp))  # raises rather than overwrite
    return {"repo": runs_repo, "stamp": stamp, "started": started,
            "commit": git("rev-parse", "HEAD").strip(),
            "uncommitted": git("status", "--porcelain").splitlines()}


def record(run, weights, meta):
    """Write the weights and `meta` into the run's directory, then commit and push it."""
    finished = time.time()
    meta = {"commit": run["commit"], "uncommitted": run["uncommitted"], **meta,
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "platform": platform.platform()},
            "started": time.strftime("%Y-%m-%dT%H:%M:%S%z",
                                     time.localtime(run["started"])),
            "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(finished)),
            "seconds": round(finished - run["started"])}
    path = os.path.join("results", run["stamp"])
    save_file(weights, os.path.join(run["repo"], path, "weights.safetensors"))
    with open(os.path.join(run["repo"], path, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    git("-C", run["repo"], "add", path)
    git("-C", run["repo"], "commit", "-m",
        f"add {run['stamp']} from {run['commit'][:7]}")
    git("-C", run["repo"], "push")
