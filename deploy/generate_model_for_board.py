"""Generate C code with ST Edge AI Core from every ONNX file of an export, and keep it.

    python3 -m deploy.generate_model_for_board stedgeai runs_repo revision onnx/<time> runs_dir [--rebuild]

`onnx/<time>` can be `window_onnx/<time>` too, and the code then goes to
`window_board/<time>`. It can also be `quantize/<time>` or `window_quantize/<time>`, and
the code is then generated from the int8 files.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile

from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from models.fits import model_from
from models.onnx_files import onnx_file_path

TARGET = "stm32h5"
# where the code goes and which files it is generated from, by the kind of directory
KINDS = {"onnx": ("board", "float"), "window_onnx": ("window_board", "float"),
         "quantize": ("board", "int8"), "window_quantize": ("window_board", "int8")}


def kept_files(name):
    """The files kept of the code generated under `name`. The generator starts every
    file but the licence with that name."""
    ends = (".c", ".h", "_data.c", "_data.h", "_details.h", "_c_info.json",
            "_generate_report.txt")
    return [f"{name}{end}" for end in ends] + ["LICENSE.txt"]


def generate(stedgeai, onnx_path, name, dest):
    """Generate C code named `name` from `onnx_path`, and copy the files kept into a new
    `dest`."""
    os.makedirs(dest)                       # raises rather than overwrite
    with tempfile.TemporaryDirectory() as scratch:
        output = os.path.join(scratch, "output")
        # "n" declines the prompt to send usage statistics
        subprocess.run([stedgeai, "generate", "--target", TARGET, "--model", onnx_path,
                        "--name", name,
                        "--workspace", os.path.join(scratch, "workspace"),
                        "--output", output],
                       input="n\n", capture_output=True, text=True, check=True)
        for kept in kept_files(name):
            shutil.copy(os.path.join(output, kept), dest)


def write_board_files(folder, stedgeai, runs_repo, revision, onnx_path, runs_dir):
    """Generate C code from each file of an export, or of its int8 files, and return
    what to record."""
    source, read = read_dir(runs_repo, onnx_path, runs_dir, revision)
    precision = KINDS[onnx_path.split("/")[0]][1]
    here = {"repo": runs_repo, "revision": revision, "path": onnx_path}
    if precision == "int8":
        # the int8 files' directory names the export, which lists the models
        export = read["onnx"]
        _, exported = read_dir(export["repo"], export["path"], runs_dir,
                               export["revision"])
        made_from = {"onnx": export, "quantize": here}
    else:
        exported, made_from = read, {"onnx": here}
    version = subprocess.run([stedgeai, "--version"], capture_output=True, text=True,
                             check=True).stdout.splitlines()[0]
    for entry in exported["exported"]:
        model = model_from(entry)
        generate(stedgeai, onnx_file_path(source, model, precision), model.C_NAME,
                 os.path.join(folder, model.onnx_name))
    return {**made_from,
            **{name: exported[name] for name in ("models", "exported")},
            "versions": {"python": platform.python_version(), "stedgeai": version}}


def main(stedgeai, runs_repo, revision, onnx_path, runs_dir, rebuild=False,
         dry_run=False):
    exported_kind = onnx_path.split("/")[0]
    if exported_kind not in KINDS:
        raise ValueError(f"{onnx_path} is not under {' or '.join(KINDS)}")
    return reuse_or_make(runs_repo, KINDS[exported_kind][0], {"onnx": onnx_path},
                         {"target": TARGET}, runs_dir,
                         lambda folder: write_board_files(folder, stedgeai, runs_repo,
                                                          revision, onnx_path, runs_dir),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("stedgeai", "runs_repo", "revision", "onnx_path", "runs_dir"),
                    rebuild=False))
