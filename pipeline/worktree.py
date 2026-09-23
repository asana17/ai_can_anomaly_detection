"""Run `pipeline.stages` on HEAD's code, checked out into a git worktree of its own.

The folders and repos come from the settings file's `pipeline`. A run gets
`snapshot_dir/<time>/`, holding the worktree as `code/` and copies of the settings
and models files, so editing this tree or those files while it runs changes nothing.
A dry run does the same in a temporary folder, removed after.
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
from common.settings import read_settings
from pipeline.stages import STAGES


def check_out(run_dir, settings, models):
    """Check HEAD out into `run_dir/code`, copy the two files beside it, and return
    `code`."""
    code = os.path.join(run_dir, "code")
    git("worktree", "add", "--detach", code, "HEAD")
    shutil.copyfile(settings, os.path.join(run_dir, "settings.json"))
    shutil.copyfile(models, os.path.join(run_dir, "models.json"))
    return code


def run_stages(code, run_dir, data_repo, can_data_dir, can_data_pattern, local_data_dir,
               runs_repo, local_runs_dir, dry_run, rebuild):
    """Run the stages in the worktree `code`, on the files copied into `run_dir`."""
    subprocess.run([sys.executable, "-m", "pipeline.stages", data_repo,
                    os.path.abspath(can_data_dir), can_data_pattern,
                    os.path.abspath(local_data_dir), runs_repo,
                    os.path.abspath(local_runs_dir),
                    os.path.join(run_dir, "settings.json"),
                    os.path.join(run_dir, "models.json"),
                    *(["--dry-run"] if dry_run else []),
                    *[flag for name in rebuild for flag in ("--rebuild", name)]],
                   cwd=code, check=True)


def main(settings, models, dry_run=False, rebuild=()):
    unknown = set(rebuild) - {stage.__name__ for stage in STAGES}
    if unknown:
        raise SystemExit(f"no stage is named {', '.join(sorted(unknown))}")
    where = read_settings(settings).pipeline
    stages = (where.data_repo, where.can_data_dir, where.can_data_pattern,
              where.local_data_dir, where.runs_repo, where.local_runs_dir)
    if dry_run:
        with tempfile.TemporaryDirectory() as run_dir:
            code = check_out(run_dir, settings, models)
            try:
                run_stages(code, run_dir, *stages, dry_run=True, rebuild=rebuild)
            finally:
                git("worktree", "remove", "--force", code)
        return
    run_dir = os.path.abspath(os.path.join(where.snapshot_dir,
                                           time.strftime("%Y%m%d-%H%M%S")))
    print(f"run in {run_dir}", flush=True)
    run_stages(check_out(run_dir, settings, models), run_dir, *stages, dry_run=False,
               rebuild=rebuild)


if __name__ == "__main__":
    main(**arguments(("settings", "models"), dry_run=False, rebuild=[]))
