"""Generate C code with ST Edge AI Core from every float ONNX file of an export, and keep it.

    python3 -m deploy.generate_model_for_board stedgeai runs_repo revision onnx/<time> runs_dir [--rebuild]
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
from models.onnx_files import onnx_file_path, onnx_name

TARGET = "stm32h5"
KEPT = ("network.c", "network.h", "network_data.c", "network_data.h",
        "network_details.h", "network_c_info.json", "network_generate_report.txt",
        "LICENSE.txt")


def generate(stedgeai, onnx_path, dest):
    """Generate C code from `onnx_path`, and copy the files kept into a new `dest`."""
    os.makedirs(dest)                       # raises rather than overwrite
    with tempfile.TemporaryDirectory() as scratch:
        output = os.path.join(scratch, "output")
        # "n" declines the prompt to send usage statistics
        subprocess.run([stedgeai, "generate", "--target", TARGET, "--model", onnx_path,
                        "--workspace", os.path.join(scratch, "workspace"),
                        "--output", output],
                       input="n\n", capture_output=True, text=True, check=True)
        for name in KEPT:
            shutil.copy(os.path.join(output, name), dest)


def write_board_files(folder, stedgeai, runs_repo, revision, onnx_path, runs_dir):
    """Generate C code from each float file of an export, and return what to record."""
    source, exported = read_dir(runs_repo, onnx_path, runs_dir, revision)
    version = subprocess.run([stedgeai, "--version"], capture_output=True, text=True,
                             check=True).stdout.splitlines()[0]
    for entry in exported["exported"]:
        model = model_from(entry)
        generate(stedgeai, onnx_file_path(source, model, "float"),
                 os.path.join(folder, onnx_name(model)))
    return {"onnx": {"repo": runs_repo, "revision": revision, "path": onnx_path},
            **{name: exported[name] for name in ("models", "exported")},
            "versions": {"python": platform.python_version(), "stedgeai": version}}


def main(stedgeai, runs_repo, revision, onnx_path, runs_dir, rebuild=False,
         dry_run=False):
    inputs = {"onnx": onnx_path, "target": TARGET}
    return reuse_or_make(runs_repo, "board", inputs, runs_dir,
                         lambda folder: write_board_files(folder, stedgeai, runs_repo,
                                                          revision, onnx_path, runs_dir),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("stedgeai", "runs_repo", "revision", "onnx_path", "runs_dir"),
                    rebuild=False))
