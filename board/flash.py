"""Headless-build and flash an already prepared CubeIDE project on macOS."""

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "flash.json"


def project_name(project_dir):
    name = ET.parse(project_dir / ".project").getroot().findtext("name")
    if not name:
        raise SystemExit(f"project name not found in {project_dir / '.project'}")
    return name


def commands(project_dir, workspace, cubeide, programmer):
    name = project_name(project_dir)
    elf = project_dir / "Debug" / f"{name}.elf"
    return (
        [str(cubeide), "--launcher.suppressErrors", "-nosplash", "-application",
         "org.eclipse.cdt.managedbuilder.core.headlessbuild", "-data", str(workspace),
         "-import", str(project_dir), "-cleanBuild", f"{name}/Debug"],
        [str(programmer), "-c", "port=SWD", "-w", str(elf), "-v", "-rst"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--config", type=Path, default=CONFIG)
    args = parser.parse_args()

    project_dir = args.project_dir.expanduser().resolve()
    config = json.loads(args.config.expanduser().read_text())
    cubeide = Path(config["cubeide"]).expanduser()
    programmer = Path(config["programmer"]).expanduser()
    with tempfile.TemporaryDirectory(prefix="cubeide-headless-") as workspace:
        for command in commands(project_dir, Path(workspace), cubeide, programmer):
            print("+", shlex.join(command), flush=True)
            subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
