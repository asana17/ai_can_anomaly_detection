"""Headless-build and flash an already prepared CubeIDE project."""

import argparse
from pathlib import Path
import shlex
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from board.paths import read_paths


def project_name(project_dir):
    name = ET.parse(project_dir / ".project").getroot().findtext("name")
    if not name:
        raise SystemExit(f"project name not found in {project_dir / '.project'}")
    return name


def commands(project_dir, workspace, cubeide, programmer):
    name = project_name(project_dir)
    elf = project_dir / "Release" / f"{name}.elf"
    return (
        [str(cubeide), "--launcher.suppressErrors", "-nosplash", "-application",
         "org.eclipse.cdt.managedbuilder.core.headlessbuild", "-data", str(workspace),
         "-import", str(project_dir), "-cleanBuild", f"{name}/Release"],
        [str(programmer), "-c", "port=SWD", "-w", str(elf), "-v", "-rst"],
    )


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    project_dir, cubeide, programmer = read_paths("project", "cubeide", "programmer")
    with tempfile.TemporaryDirectory(prefix="cubeide-headless-") as workspace:
        for command in commands(project_dir, Path(workspace), cubeide, programmer):
            print("+", shlex.join(command), flush=True)
            subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
