"""Pure transformations of CubeMX/CubeIDE project files."""

import random
import xml.etree.ElementTree as ET

from .application import LIB, TEST_COMMON

MARKER = "/* USER CODE BEGIN WHILE */"
START = ("void knl_start_mtkernel(void);", "knl_start_mtkernel();")
COMPILE_TOOLS = ("com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.assembler",
                 "com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.compiler")
LINKER_TOOL = "com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.linker"
DEFINES = ("_STM32CUBE_NUCLEO_H533_", "UNITY_INCLUDE_CONFIG_H")
INCLUDES = ("mtk3_bsp2", "mtk3_bsp2/config", "mtk3_bsp2/include",
            "mtk3_bsp2/mtkernel/kernel/knlinc", "test_common", "Unity/src")
SOURCES = ("mtk3_bsp2", "Unity/src", "application", "test_common")


def start_kernel(main_c):
    if START[1] in main_c:
        return main_c
    if MARKER not in main_c:
        raise ValueError(f"no {MARKER} in main.c")
    newline = "\r\n" if "\r\n" in main_c else "\n"
    added = "".join(f"{newline}  {line}" for line in START)
    return main_c.replace(MARKER, MARKER + added, 1)


def _parse(text, root_tag):
    at = text.index(f"<{root_tag}")
    return text[:at], ET.fromstring(text[at:])


def _write(head, root):
    ET.indent(root, space="\t")
    return head + ET.tostring(root, encoding="unicode") + "\n"


def _list_option(tool, kind, name, value_type):
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


def _remove_values(option, predicate):
    for value in list(option.findall("listOptionValue")):
        if predicate(value.get("value", "")):
            option.remove(value)


def _workspace_path(path):
    return f'"${{workspace_loc:/${{ProjName}}/{path}}}"'


def configure(cproject, libraries=(), include_dirs=(), runtime=None):
    """Select sources/includes and, when needed, the st-ai runtime."""
    head, root = _parse(cproject, "cproject")
    library_paths = tuple(f"lib/{library}" for library in libraries)
    project_includes = INCLUDES + library_paths + tuple(include_dirs)
    for tool in root.iter("tool"):
        if tool.get("superClass") in COMPILE_TOOLS:
            defines = _list_option(tool, "definedsymbols", "Define symbols (-D)",
                                   "definedSymbols")
            for define in DEFINES:
                _add_value(defines, define)
            includes = _list_option(tool, "includepaths", "Include paths (-I)", "includePath")
            _remove_values(includes, lambda path: ("/${ProjName}/common}" in path or
                                                   "/${ProjName}/lib/" in path or
                                                   "/${ProjName}/application/" in path or
                                                   path.endswith("/Middlewares/ST/AI/Inc\"")))
            for path in project_includes:
                _add_value(includes, _workspace_path(path))
            if runtime:
                _add_value(includes, f'"{runtime.include_dir}"')
        elif tool.get("superClass") == LINKER_TOOL:
            libraries_option = _list_option(tool, "libraries", "Libraries (-l)", "libs")
            directories = _list_option(tool, "directories", "Library search path (-L)",
                                       "libPaths")
            _remove_values(libraries_option, lambda value: "NetworkRuntime" in value)
            _remove_values(directories, lambda value: "Middlewares/ST/AI/Lib/" in value)
            if runtime:
                _add_value(libraries_option, f":{runtime.library}")
                _add_value(directories, runtime.library_dir)
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
        ET.SubElement(link, "type").text = "2"
        ET.SubElement(link, "location").text = location
    return _write(head, root)


def link_folders(project, app_dir):
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


def rewrite(path, change):
    with open(path, newline="") as file:
        before = file.read()
    after = change(before)
    if after == before:
        return False
    with open(path, "w", newline="") as file:
        file.write(after)
    return True
