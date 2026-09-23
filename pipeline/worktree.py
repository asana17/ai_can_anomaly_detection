"""Run `pipeline.stages` on HEAD's code, checked out into a git worktree of its own.

A run gets `work_dir/<time>/`, holding the worktree as `code/` and copies of the
settings and models files, so editing this tree or those files while it runs changes
nothing. A dry run does the same in a temporary folder, removed after.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time

from common.cli import arguments
from common.git import git


def check_out(run_dir, settings, models):
    """Check HEAD out into `run_dir/code`, copy the two files beside it, and return
    `code`."""
    code = os.path.join(run_dir, "code")
    git("worktree", "add", "--detach", code, "HEAD")
    shutil.copyfile(settings, os.path.join(run_dir, "settings.json"))
    shutil.copyfile(models, os.path.join(run_dir, "models.json"))
    return code


def run_stages(code, run_dir, repo, data_dir, pattern, local_dir, runs_repo, runs_dir,
               dry_run):
    """Run the stages in the worktree `code`, on the files copied into `run_dir`."""
    subprocess.run([sys.executable, "-m", "pipeline.stages", repo,
                    os.path.abspath(data_dir), pattern, os.path.abspath(local_dir),
                    runs_repo, os.path.abspath(runs_dir),
                    os.path.join(run_dir, "settings.json"),
                    os.path.join(run_dir, "models.json"),
                    *(["--dry-run"] if dry_run else [])],
                   cwd=code, check=True)


def main(work_dir, repo, data_dir, pattern, local_dir, runs_repo, runs_dir, settings,
         models, dry_run=False):
    stages = (repo, data_dir, pattern, local_dir, runs_repo, runs_dir)
    if dry_run:
        with tempfile.TemporaryDirectory() as run_dir:
            code = check_out(run_dir, settings, models)
            try:
                run_stages(code, run_dir, *stages, dry_run=True)
            finally:
                git("worktree", "remove", "--force", code)
        return
    run_dir = os.path.abspath(os.path.join(work_dir, time.strftime("%Y%m%d-%H%M%S")))
    print(f"run in {run_dir}", flush=True)
    run_stages(check_out(run_dir, settings, models), run_dir, *stages, dry_run=False)


if __name__ == "__main__":
    main(**arguments(("work_dir", "repo", "data_dir", "pattern", "local_dir",
                      "runs_repo", "runs_dir", "settings", "models"), dry_run=False))
