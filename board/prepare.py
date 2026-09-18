"""Add mtk3_bsp2 and our application to a CubeMX project, and start μT-Kernel from `main`.

    python3 board/prepare.py project_dir

Run it before the project is imported into CubeIDE, which rewrites `.cproject` and
`.project` while the project is open.
"""

from __future__ import annotations

import glob
import os
import random
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
BSP_URL = "https://github.com/tron-forum/mtk3_bsp2.git"
BSP_BASE = "1ab52cc"
PATCHES = sorted(glob.glob(os.path.join(HERE, "patches", "*.patch")))
APP = os.path.join(HERE, "application")
MARKER = "/* USER CODE BEGIN WHILE */"
START = ("void knl_start_mtkernel(void);", "knl_start_mtkernel();")
TOOLS = ("com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.assembler",
         "com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.compiler")
DEFINE = "_STM32CUBE_NUCLEO_H533_"
INCLUDES = ("mtk3_bsp2", "mtk3_bsp2/config", "mtk3_bsp2/include",
            "mtk3_bsp2/mtkernel/kernel/knlinc")
LINK = "application"
SOURCES = ("mtk3_bsp2", LINK)


def git(*args):
    subprocess.run(["git", *args], capture_output=True, text=True, check=True)


def add_bsp(project_dir):
    """Clone mtk3_bsp2 at `BSP_BASE` with our patches, or check that a clone has them.

    The kernel itself is the submodule `mtkernel`, checked out at the commit `BSP_BASE`
    records.
    """
    bsp = os.path.join(project_dir, "mtk3_bsp2")
    if not os.path.exists(bsp):
        git("clone", BSP_URL, bsp)
        git("-C", bsp, "checkout", BSP_BASE)
        # the sources end lines in CRLF, which `am` strips by default
        git("-C", bsp, "am", "--keep-cr", *PATCHES)
        done = "cloned"
    else:
        for patch in PATCHES:
            try:
                git("-C", bsp, "apply", "--reverse", "--check", patch)
            except subprocess.CalledProcessError:
                raise SystemExit(f"{bsp} lacks {os.path.basename(patch)}")
        done = "already there"
    git("-C", bsp, "submodule", "update", "--init")
    return done


def start_kernel(main_c):
    """`main_c` with the kernel started right after `BSP_COM_Init()`.

    `USER CODE` blocks survive CubeMX generating again, and `USER CODE BEGIN WHILE` is the
    first one after `BSP_COM_Init()`.
    """
    if START[1] in main_c:
        return main_c
    if MARKER not in main_c:
        raise ValueError(f"no {MARKER} in main.c")
    newline = "\r\n" if "\r\n" in main_c else "\n"
    added = "".join(f"{newline}  {line}" for line in START)
    return main_c.replace(MARKER, MARKER + added, 1)


def _parse(text, root_tag):
    """The declarations before the root element, which ElementTree drops, and the root."""
    at = text.index(f"<{root_tag}")
    return text[:at], ET.fromstring(text[at:])


def _write(head, root):
    ET.indent(root, space="\t")
    return head + ET.tostring(root, encoding="unicode") + "\n"


def _list_option(tool, kind, name, value_type):
    """The tool's option of `kind`, added the way CubeIDE writes it when missing."""
    super_class = f"{tool.get('superClass')}.option.{kind}"
    for option in tool.findall("option"):
        if option.get("superClass") == super_class:
            return option
    option = ET.Element("option", {
        "IS_BUILTIN_EMPTY": "false", "IS_VALUE_EMPTY": "false",
        "id": f"{super_class}.{random.randrange(10**9)}", "name": name,
        "superClass": super_class, "valueType": value_type})
    tags = [child.tag for child in tool]
    tool.insert(tags.index("inputType") if "inputType" in tags else len(tags), option)
    return option


def _add_value(option, value):
    if value not in [v.get("value") for v in option.findall("listOptionValue")]:
        ET.SubElement(option, "listOptionValue", {"builtIn": "false", "value": value})


def configure(cproject):
    """`.cproject` with the define, include paths and source folders mtk3_bsp2 needs.

    Every build configuration gets them, the same as Properties, Paths and Symbols.
    """
    head, root = _parse(cproject, "cproject")
    for tool in root.iter("tool"):
        if tool.get("superClass") not in TOOLS:
            continue
        _add_value(_list_option(tool, "definedsymbols", "Define symbols (-D)",
                                "definedSymbols"), DEFINE)
        includes = _list_option(tool, "includepaths", "Include paths (-I)", "includePath")
        for path in INCLUDES:
            _add_value(includes, f'"${{workspace_loc:/${{ProjName}}/{path}}}"')
    for entries in root.iter("sourceEntries"):
        names = [entry.get("name") for entry in entries]
        for name in SOURCES:
            if name not in names:
                ET.SubElement(entries, "entry", {"flags": "VALUE_WORKSPACE_PATH",
                                                 "kind": "sourcePath", "name": name})
    return _write(head, root)


def link_app(project, app=APP):
    """`.project` with the folder `LINK` linked to `app`, our application.

    A link already there is pointed at `app`, in case this repository moved.
    """
    head, root = _parse(project, "projectDescription")
    links = root.find("linkedResources")
    if links is None:
        links = ET.SubElement(root, "linkedResources")
    for link in links:
        if link.findtext("name") == LINK:
            link.find("location").text = app
            break
    else:
        link = ET.SubElement(links, "link")
        ET.SubElement(link, "name").text = LINK
        ET.SubElement(link, "type").text = "2"      # a folder
        ET.SubElement(link, "location").text = app
    return _write(head, root)


def _rewrite(path, change):
    """Apply `change` to the file, and say whether it changed anything."""
    with open(path, newline="") as f:
        before = f.read()
    after = change(before)
    if after == before:
        return False
    with open(path, "w", newline="") as f:
        f.write(after)
    return True


def main(project_dir):
    path = os.path.join(project_dir, "Core", "Src", "main.c")
    if not os.path.exists(path):
        raise SystemExit(f"no {path}, is {project_dir} the directory with the .ioc?")
    print(f"mtk3_bsp2: {add_bsp(project_dir)}")
    for name, file, change in (("main.c", path, start_kernel),
                               (".cproject", os.path.join(project_dir, ".cproject"), configure),
                               (".project", os.path.join(project_dir, ".project"), link_app)):
        print(f"{name}: {'changed' if _rewrite(file, change) else 'already done'}")


if __name__ == "__main__":
    main(sys.argv[1])
