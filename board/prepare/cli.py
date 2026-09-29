"""Select one application and prepare a generated CubeIDE project for it.

    python3 -m board.prepare application_dir

The CubeIDE project and the ST Edge AI and mbed-crypto roots come from `board/paths.json`.

The command only consumes local application/model inputs. Fetching or generating a
model belongs to the deployment pipeline, not to project preparation.
"""

import argparse
import glob
import os
import shutil

from board.paths import read_paths

from .application import HERE, application_dir, application_for
from .cubeide import (LINKER_SCRIPT, configure, keep_program_in_bank_1, link_folders, rewrite,
                      start_kernel)
from .dependencies import add_bsp, add_unity, mbed_crypto, stedgeai_runtime

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


def main(application):
    project_dir, = read_paths("project")
    project_dir = str(project_dir)
    main_c = os.path.join(project_dir, "Core", "Src", "main.c")
    if not os.path.exists(main_c):
        raise SystemExit(f"no {main_c}, is {project_dir} the directory with the .ioc?")
    app_dir = application_dir(application)
    selected = application_for(app_dir)
    runtime = stedgeai_runtime(*read_paths("stedgeai")) if selected.needs_stedgeai else None
    crypto = mbed_crypto(*read_paths("mbed_crypto")) if selected.needs_mbed_crypto else None

    print(f".ioc: {keep_ioc(project_dir)}")
    print(f"mtk3_bsp2: {add_bsp(project_dir)}")
    print(f"Unity: {add_unity(project_dir)}")
    changes = (
        ("main.c", main_c, start_kernel),
        (LINKER_SCRIPT, os.path.join(project_dir, LINKER_SCRIPT), keep_program_in_bank_1),
        (".cproject", os.path.join(project_dir, ".cproject"),
         lambda text: configure(text, selected.libraries, runtime, crypto)),
        (".project", os.path.join(project_dir, ".project"),
         lambda text: link_folders(text, app_dir, crypto)),
    )
    for name, path, change in changes:
        print(f"{name}: {'changed' if rewrite(path, change) else 'already done'}")


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("application_dir")
    args = parser.parse_args()
    main(args.application_dir)
