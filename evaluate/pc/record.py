"""Keep each run of the comparison in the runs repository.

`start_run` claims `results/<start time>/` when the run starts and notes the code it
starts from. `end_run` writes the weights and the numbers into it at the end, and
uploads it.
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

from common.hub_dirs import claim, upload


def git(*args):
    """What a git command prints."""
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout


def start_run(runs_repo, runs_dir):
    """Claim `results/<start time>/`, and note the code the run starts from."""
    started = time.time()
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(started))
    path = f"results/{stamp}"
    os.makedirs(claim(runs_repo, path, runs_dir))
    return {"repo": runs_repo, "dir": runs_dir, "path": path, "stamp": stamp,
            "started": started,
            "commit": git("rev-parse", "HEAD").strip(),
            "uncommitted": git("status", "--porcelain").splitlines()}


def end_run(run, weights, meta):
    """Write the weights and `meta`, and add them to the runs repository."""
    finished = time.time()
    meta = {"commit": run["commit"], "uncommitted": run["uncommitted"], **meta,
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "platform": platform.platform()},
            "started": time.strftime("%Y-%m-%dT%H:%M:%S%z",
                                     time.localtime(run["started"])),
            "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(finished)),
            "seconds": round(finished - run["started"])}
    folder = os.path.join(run["dir"], run["path"])
    save_file(weights, os.path.join(folder, "weights.safetensors"))
    with open(os.path.join(folder, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    upload(run["repo"], run["path"], run["dir"],
           f"add {run['stamp']} from {run['commit'][:7]}")
