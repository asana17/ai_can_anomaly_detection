"""Generate C code with ST Edge AI Core from every float ONNX file of an export, and keep it.

    python3 -m deploy.generate stedgeai runs_repo runs_dir onnx/<time>
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time

from common.git import git
from common.hub_dirs import claim, download, upload
from deploy.export import file_of
from models.fits import model_from

TARGET = "stm32h5"
KEPT = ("network.c", "network.h", "network_data.c", "network_data.h",
        "network_details.h", "network_c_info.json", "network_generate_report.txt",
        "LICENSE.txt")


def models_in(export_dir):
    """Every model the export lists, in its order."""
    with open(os.path.join(export_dir, "meta.json")) as f:
        return [model_from(entry) for entry in json.load(f)["exported"]]


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


def main(stedgeai, runs_repo, runs_dir, export):
    generated = time.localtime()
    stamp = time.strftime("%Y%m%d-%H%M%S", generated)
    path = f"board/{stamp}"
    dest = claim(runs_repo, path, runs_dir)
    commit = git("rev-parse", "HEAD").strip()
    uncommitted = git("status", "--porcelain").splitlines()
    export_dir = download(runs_repo, export, runs_dir)
    with open(os.path.join(export_dir, "meta.json")) as f:
        exported = json.load(f)
    models = models_in(export_dir)
    version = subprocess.run([stedgeai, "--version"], capture_output=True, text=True,
                             check=True).stdout.splitlines()[0]

    meta = {"export": export, "models": exported["models"], "target": TARGET,
            "exported": exported["exported"],
            "commit": commit, "uncommitted": uncommitted,
            "versions": {"python": platform.python_version(), "stedgeai": version},
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z", generated)}
    os.makedirs(dest)
    for model in models:
        name = file_of(model)
        generate(stedgeai, os.path.join(export_dir, f"{name}_float.onnx"),
                 os.path.join(dest, name))
    with open(os.path.join(dest, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    upload(runs_repo, path, runs_dir, f"add {path} from {export}, {len(models)} models")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
