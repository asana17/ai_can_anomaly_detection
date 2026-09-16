"""Generate C code with ST Edge AI Core from every float ONNX file of an export, and keep it.

    python3 -m quantize.generate stedgeai runs_clone exported
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

from evaluate.pc.record import git

TARGET = "stm32h5"
KEPT = ("network.c", "network.h", "network_data.c", "network_data.h",
        "network_details.h", "network_c_info.json", "network_generate_report.txt",
        "LICENSE.txt")


def models_in(export_dir):
    """The `k` and `h` of every model the export lists."""
    with open(os.path.join(export_dir, "meta.json")) as f:
        return [(m["k"], m["h"]) for m in json.load(f)["models"]]


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


def main(stedgeai, runs_clone, exported):
    generated = time.localtime()
    stamp = time.strftime("%Y%m%d-%H%M%S", generated)
    commit = git("rev-parse", "HEAD").strip()
    uncommitted = git("status", "--porcelain").splitlines()
    export = os.path.join("quantize", exported)
    export_dir = os.path.join(runs_clone, export)
    with open(os.path.join(export_dir, "meta.json")) as f:
        run = json.load(f)["run"]
    models = models_in(export_dir)
    version = subprocess.run([stedgeai, "--version"], capture_output=True, text=True,
                             check=True).stdout.splitlines()[0]

    path = os.path.join("board", stamp)
    dest = os.path.join(runs_clone, path)
    os.makedirs(dest)                       # raises rather than overwrite a generation
    for k, h in models:
        name = f"nonlinear_ae_k{k}_h{h}"
        generate(stedgeai, os.path.join(export_dir, f"{name}_float.onnx"),
                 os.path.join(dest, name))

    meta = {"export": export, "run": run, "target": TARGET,
            "models": [{"k": k, "h": h} for k, h in models],
            "commit": commit, "uncommitted": uncommitted,
            "versions": {"python": platform.python_version(), "stedgeai": version},
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z", generated)}
    with open(os.path.join(dest, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    git("-C", runs_clone, "add", path)
    git("-C", runs_clone, "commit", "-m",
        f"add {path} from {export}, {len(models)} models")
    git("-C", runs_clone, "push")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
