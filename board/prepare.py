"""Add mtk3_bsp2, Unity, selected libraries, test helpers and one application
to a CubeMX project, and start μT-Kernel.

    python3 board/prepare.py project_dir app

`app` is a folder of `board/application/`. Running it again with another `app` switches
the project to that one.

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
UNITY_URL = "https://github.com/ThrowTheSwitch/Unity.git"
UNITY_BASE = "b6763fb"     # v2.7.0
PATCHES = sorted(glob.glob(os.path.join(HERE, "patches", "*.patch")))
APPS = os.path.join(HERE, "application")
LIB = os.path.join(HERE, "lib")
TEST_COMMON = os.path.join(HERE, "test_common")
APP_LIBS = {
    "alive": (),
    "mbf_test": ("mbf",),
    "rule_check_from_flash": ("mbf",),
}
MARKER = "/* USER CODE BEGIN WHILE */"
START = ("void knl_start_mtkernel(void);", "knl_start_mtkernel();")
TOOLS = ("com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.assembler",
         "com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.compiler")
DEFINES = ("_STM32CUBE_NUCLEO_H533_",
           "UNITY_INCLUDE_CONFIG_H")    # Unity reads test_common/unity_config.h
INCLUDES = ("mtk3_bsp2", "mtk3_bsp2/config", "mtk3_bsp2/include",
            "mtk3_bsp2/mtkernel/kernel/knlinc", "test_common", "Unity/src")
SOURCES = ("mtk3_bsp2", "Unity/src", "application", "test_common")


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


def add_unity(project_dir):
    """Clone Unity at `UNITY_BASE`, or check that a clone is at it."""
    unity = os.path.join(project_dir, "Unity")
    if not os.path.exists(unity):
        git("clone", UNITY_URL, unity)
        git("-C", unity, "checkout", UNITY_BASE)
        return "cloned"
    try:
        git("-C", unity, "diff", "--quiet", UNITY_BASE)
    except subprocess.CalledProcessError:
        raise SystemExit(f"{unity} is not at {UNITY_BASE}")
    return "already there"


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


def configure(cproject, libraries=()):
    """`.cproject` with the selected libraries and the paths mtk3_bsp2 needs.

    Every build configuration gets them, the same as Properties, Paths and Symbols.
    """
    head, root = _parse(cproject, "cproject")
    library_paths = tuple(f"lib/{library}" for library in libraries)
    include_paths = INCLUDES + library_paths
    for tool in root.iter("tool"):
        if tool.get("superClass") not in TOOLS:
            continue
        defines = _list_option(tool, "definedsymbols", "Define symbols (-D)", "definedSymbols")
        for define in DEFINES:
            _add_value(defines, define)
        includes = _list_option(tool, "includepaths", "Include paths (-I)", "includePath")
        for value in list(includes):
            path = value.get("value", "")
            if "/${ProjName}/common}" in path or "/${ProjName}/lib/" in path:
                includes.remove(value)
        for path in include_paths:
            _add_value(includes, f'"${{workspace_loc:/${{ProjName}}/{path}}}"')
    for entries in root.iter("sourceEntries"):
        for entry in list(entries):
            name = entry.get("name", "")
            if name == "common" or name.startswith("lib/"):
                entries.remove(entry)
        names = [entry.get("name") for entry in entries]
        for name in SOURCES + library_paths:
            if name not in names:
                ET.SubElement(entries, "entry", {"flags": "VALUE_WORKSPACE_PATH",
                                                 "kind": "sourcePath", "name": name})
    return _write(head, root)


def link_folder(project, name, location):
    """`.project` with the folder `name` linked to `location`.

    A link already there is pointed at `location`, in case this repository moved or another
    application is chosen.
    """
    head, root = _parse(project, "projectDescription")
    links = root.find("linkedResources")
    if links is None:
        links = ET.SubElement(root, "linkedResources")
    for link in links:
        if link.findtext("name") == name:
            link.find("location").text = location
            break
    else:
        link = ET.SubElement(links, "link")
        ET.SubElement(link, "name").text = name
        ET.SubElement(link, "type").text = "2"      # a folder
        ET.SubElement(link, "location").text = location
    return _write(head, root)


def link_folders(project, app_dir):
    """`.project` with `application`, `lib` and `test_common` linked."""
    head, root = _parse(project, "projectDescription")
    links = root.find("linkedResources")
    if links is not None:
        for link in list(links):
            if link.findtext("name") == "common":
                links.remove(link)
    project = _write(head, root)
    for name, location in (("application", app_dir), ("lib", LIB),
                           ("test_common", TEST_COMMON)):
        project = link_folder(project, name, location)
    return project


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


def main(project_dir, app):
    path = os.path.join(project_dir, "Core", "Src", "main.c")
    if not os.path.exists(path):
        raise SystemExit(f"no {path}, is {project_dir} the directory with the .ioc?")
    app_dir = os.path.join(APPS, app)
    if not os.path.isdir(app_dir):
        raise SystemExit(f"no {app_dir}, the applications are "
                         f"{', '.join(sorted(os.listdir(APPS)))}")
    if app not in APP_LIBS:
        raise SystemExit(f"no library selection for application {app}")
    libraries = APP_LIBS[app]
    print(f"mtk3_bsp2: {add_bsp(project_dir)}")
    print(f"Unity: {add_unity(project_dir)}")
    for name, file, change in (("main.c", path, start_kernel),
                               (".cproject", os.path.join(project_dir, ".cproject"),
                                lambda text: configure(text, libraries)),
                               (".project", os.path.join(project_dir, ".project"),
                                lambda text: link_folders(text, app_dir))):
        print(f"{name}: {'changed' if _rewrite(file, change) else 'already done'}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
