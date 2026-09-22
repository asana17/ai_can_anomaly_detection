"""Select one application and prepare a generated CubeIDE project for it.

    python3 -m board.prepare project_dir application_dir [--stedgeai-root PATH]

The command only consumes local application/model inputs. Fetching or generating a
model belongs to the deployment pipeline, not to project preparation.
"""

import argparse
import glob
import os
import shutil

from .application import HERE, application_dir, application_for
from .cubeide import configure, link_folders, rewrite, start_kernel
from .dependencies import DEFAULT_STEDGEAI, add_bsp, add_unity, stedgeai_runtime

CUBEMX = os.path.join(HERE, "cubemx")


def keep_ioc(project_dir):
    """Copy the project's `.ioc` into the repository, and say what that took.

    The CubeMX project lives outside the repository, so its settings would be lost
    with it. Preparing is the step every build goes through, so the copy is taken
    here and a change to the settings shows up in `git status`.
    """
    found = glob.glob(os.path.join(project_dir, "*.ioc"))
    if len(found) != 1:
        raise SystemExit(f"expected one .ioc in {project_dir}, found {len(found)}")
    kept = os.path.join(CUBEMX, os.path.basename(found[0]))
    os.makedirs(CUBEMX, exist_ok=True)
    if os.path.isfile(kept) and open(kept, newline="").read() == open(found[0], newline="").read():
        return "already there"
    shutil.copy(found[0], kept)
    return "copied"


def main(project_dir, application, stedgeai_root=None):
    project_dir = os.path.abspath(os.path.expanduser(project_dir))
    main_c = os.path.join(project_dir, "Core", "Src", "main.c")
    if not os.path.exists(main_c):
        raise SystemExit(f"no {main_c}, is {project_dir} the directory with the .ioc?")
    app_dir = application_dir(application)
    selected = application_for(app_dir)
    runtime = stedgeai_runtime(stedgeai_root) if selected.needs_stedgeai else None

    print(f".ioc: {keep_ioc(project_dir)}")
    print(f"mtk3_bsp2: {add_bsp(project_dir)}")
    print(f"Unity: {add_unity(project_dir)}")
    changes = (
        ("main.c", main_c, start_kernel),
        (".cproject", os.path.join(project_dir, ".cproject"),
         lambda text: configure(text, selected.libraries, runtime)),
        (".project", os.path.join(project_dir, ".project"),
         lambda text: link_folders(text, app_dir)),
    )
    for name, path, change in changes:
        print(f"{name}: {'changed' if rewrite(path, change) else 'already done'}")


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir")
    parser.add_argument("application_dir")
    parser.add_argument("--stedgeai-root", default=None,
                        help=f"ST Edge AI v4.0 root (default: STEDGEAI_ROOT or {DEFAULT_STEDGEAI})")
    args = parser.parse_args()
    main(args.project_dir, args.application_dir, args.stedgeai_root)
