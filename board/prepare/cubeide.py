"""Pure transformations of CubeMX/CubeIDE project files."""

import os
import random
import re
import xml.etree.ElementTree as ET

from .application import LIB, TEST_COMMON

MARKER = "/* USER CODE BEGIN WHILE */"
START = ("void knl_start_mtkernel(void);", "knl_start_mtkernel();")
COMPILE_TOOLS = ("com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.assembler",
                 "com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.compiler")
C_COMPILER = COMPILE_TOOLS[1]
LINKER_TOOL = "com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.linker"
# float32 math rounds as numpy does, the product before the sum, which GCC's FMA does not
C_FLAGS = ("-ffp-contract=off",)
DEFINES = ("_STM32CUBE_NUCLEO_H533_", "UNITY_INCLUDE_CONFIG_H")
INCLUDES = ("mtk3_bsp2", "mtk3_bsp2/config", "mtk3_bsp2/include",
            "mtk3_bsp2/mtkernel/kernel/knlinc", "test_common", "Unity/src")
SOURCES = ("mtk3_bsp2", "Unity/src", "application", "test_common")
MBED_CRYPTO_FOLDER = "mbed-crypto"
MBED_CRYPTO_CONFIG = "MBEDTLS_CONFIG_FILE=<alarm_frames_mac_mbedtls_config.h>"
LINKER_SCRIPT = "STM32H533RETX_FLASH.ld"
# bank 2 keeps the alarm cuts, so the program stays in bank 1
FLASH_LENGTH = re.compile(r"(FLASH\s*\(rx\)\s*:\s*ORIGIN = 0x08000000,\s*LENGTH = )\d+K")
BANK_1 = "256K"


def start_kernel(main_c):
    if START[1] in main_c:
        return main_c
    if MARKER not in main_c:
        raise ValueError(f"no {MARKER} in main.c")
    newline = "\r\n" if "\r\n" in main_c else "\n"
    added = "".join(f"{newline}  {line}" for line in START)
    return main_c.replace(MARKER, MARKER + added, 1)


def keep_program_in_bank_1(linker_script):
    if not FLASH_LENGTH.search(linker_script):
        raise ValueError(f"no FLASH region at 0x08000000 in {LINKER_SCRIPT}")
    return FLASH_LENGTH.sub(rf"\g<1>{BANK_1}", linker_script, count=1)


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


def configure(cproject, libraries=(), runtime=None, mbed_crypto=None):
    """Select sources/includes and, when needed, the st-ai runtime and mbed-crypto."""
    head, root = _parse(cproject, "cproject")
    library_paths = tuple(f"lib/{library}" for library in libraries)
    source_paths = SOURCES + library_paths + ((MBED_CRYPTO_FOLDER,) if mbed_crypto else ())
    project_includes = INCLUDES + library_paths
    for tool in root.iter("tool"):
        if tool.get("superClass") in COMPILE_TOOLS:
            defines = _list_option(tool, "definedsymbols", "Define symbols (-D)",
                                   "definedSymbols")
            _remove_values(defines, lambda value: value.startswith("MBEDTLS_CONFIG_FILE="))
            for define in DEFINES:
                _add_value(defines, define)
            if mbed_crypto:
                _add_value(defines, MBED_CRYPTO_CONFIG)
            includes = _list_option(tool, "includepaths", "Include paths (-I)", "includePath")
            _remove_values(includes, lambda path: ("/${ProjName}/common}" in path or
                                                   "/${ProjName}/lib/" in path or
                                                   "/${ProjName}/application/" in path or
                                                   path.endswith("/Middlewares/ST/AI/Inc\"") or
                                                   path.endswith("/mbed-crypto/include\"")))
            for path in project_includes:
                _add_value(includes, _workspace_path(path))
            if runtime:
                _add_value(includes, f'"{runtime.include_dir}"')
            if mbed_crypto:
                _add_value(includes, f'"{mbed_crypto.include_dir}"')
            if tool.get("superClass") == C_COMPILER:
                flags = _list_option(tool, "otherflags", "Other flags", "stringList")
                for flag in C_FLAGS:
                    _add_value(flags, flag)
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
            if name in ("common", MBED_CRYPTO_FOLDER) or name.startswith("lib/"):
                entries.remove(entry)
        names = [entry.get("name") for entry in entries]
        for name in source_paths:
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


def link_files(project, folder, paths):
    """Link each path as a file in a virtual folder, or drop the folder when none."""
    head, root = _parse(project, "projectDescription")
    links = root.find("linkedResources")
    if links is None:
        links = ET.SubElement(root, "linkedResources")
    for link in list(links):
        name = link.findtext("name", "")
        if name == folder or name.startswith(f"{folder}/"):
            links.remove(link)
    if paths:
        link = ET.SubElement(links, "link")
        ET.SubElement(link, "name").text = folder
        ET.SubElement(link, "type").text = "2"
        ET.SubElement(link, "locationURI").text = "virtual:/virtual"
    for path in paths:
        link = ET.SubElement(links, "link")
        ET.SubElement(link, "name").text = f"{folder}/{os.path.basename(path)}"
        ET.SubElement(link, "type").text = "1"
        ET.SubElement(link, "location").text = path
    return _write(head, root)


def link_folders(project, app_dir, mbed_crypto=None):
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
    return link_files(project, MBED_CRYPTO_FOLDER, mbed_crypto.sources if mbed_crypto else ())


def rewrite(path, change):
    with open(path, newline="") as file:
        before = file.read()
    after = change(before)
    if after == before:
        return False
    with open(path, "w", newline="") as file:
        file.write(after)
    return True
