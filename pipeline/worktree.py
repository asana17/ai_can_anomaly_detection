"""Run `pipeline.stages` on HEAD's code, checked out into a git worktree of its own.

A run gets `work_dir/<time>/`, holding the worktree as `code/` and copies of the
settings and models files, so editing this tree or those files while it runs changes
nothing.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time

from common.cli import arguments
from common.git import git


def main(work_dir, repo, data_dir, pattern, local_dir, runs_repo, runs_dir, settings,
         models):
    run_dir = os.path.abspath(os.path.join(work_dir, time.strftime("%Y%m%d-%H%M%S")))
    print(f"run in {run_dir}", flush=True)
    code = os.path.join(run_dir, "code")
    git("worktree", "add", "--detach", code, "HEAD")
    shutil.copyfile(settings, os.path.join(run_dir, "settings.json"))
    shutil.copyfile(models, os.path.join(run_dir, "models.json"))
    subprocess.run([sys.executable, "-m", "pipeline.stages", repo,
                    os.path.abspath(data_dir), pattern, os.path.abspath(local_dir),
                    runs_repo, os.path.abspath(runs_dir),
                    os.path.join(run_dir, "settings.json"),
                    os.path.join(run_dir, "models.json")],
                   cwd=code, check=True)


if __name__ == "__main__":
    main(**arguments(("work_dir", "repo", "data_dir", "pattern", "local_dir",
                      "runs_repo", "runs_dir", "settings", "models")))
