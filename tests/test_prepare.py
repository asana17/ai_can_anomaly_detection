import xml.etree.ElementTree as ET

import pytest

from board.prepare.application import (LIB, MODEL_FILES, TEST_COMMON, application_dir,
                                       application_for)
from board.prepare.cubeide import (COMPILE_TOOLS, DEFINES, LINKER_TOOL, MARKER,
                                   configure, link_folder, link_folders, start_kernel)
from board.prepare.dependencies import stedgeai_runtime

MAIN_C = ("  }\r\n"
          "\r\n"
          f"  {MARKER}\r\n"
          "  while (1)\r\n")


def test_the_kernel_starts_right_after_the_marker():
    assert start_kernel(MAIN_C) == ("  }\r\n"
                                    "\r\n"
                                    f"  {MARKER}\r\n"
                                    "  void knl_start_mtkernel(void);\r\n"
                                    "  knl_start_mtkernel();\r\n"
                                    "  while (1)\r\n")


def test_lf_files_get_lf():
    added = start_kernel(MAIN_C.replace("\r\n", "\n"))
    assert "\r" not in added
    assert "knl_start_mtkernel();\n" in added


def test_a_second_run_changes_nothing():
    once = start_kernel(MAIN_C)
    assert start_kernel(once) == once


def test_application_can_be_an_arbitrary_directory(tmp_path):
    app = tmp_path / "test_application" / "mbf_test"
    app.mkdir(parents=True)
    assert application_dir(str(app)) == str(app)


def test_model_application_requires_the_fixed_generated_inputs(tmp_path):
    app = tmp_path / "model_check_from_flash"
    generated = app / "generated"
    generated.mkdir(parents=True)
    with pytest.raises(SystemExit, match="active_model.c"):
        application_for(str(app))
    for name in MODEL_FILES:
        (generated / name).touch()
    selected = application_for(str(app))
    assert selected.libraries == ("mbf", "scale", "model")
    assert selected.include_dirs == ("application/generated",)


def test_stedgeai_runtime_requires_header_and_cm33_archive(tmp_path):
    include = tmp_path / "Middlewares/ST/AI/Inc"
    library = tmp_path / "Middlewares/ST/AI/Lib/GCC/ARMCortexM33"
    include.mkdir(parents=True)
    library.mkdir(parents=True)
    (include / "stai.h").touch()
    (library / "NetworkRuntime1201_CM33_GCC.a").touch()
    runtime = stedgeai_runtime(str(tmp_path))
    assert runtime.include_dir == str(include)
    assert runtime.library_dir == str(library)


def test_no_marker_is_an_error():
    with pytest.raises(ValueError):
        start_kernel("int main(void)\r\n{\r\n}\r\n")


CPROJECT = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?fileVersion 4.0.0?><cproject>
\t<tool superClass="com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.assembler">
\t\t<inputType id="in"/>
\t</tool>
\t<tool superClass="com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.compiler">
\t\t<option superClass="com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.compiler.option.definedsymbols">
\t\t\t<listOptionValue builtIn="false" value="DEBUG"/>
\t\t</option>
\t</tool>
\t<tool superClass="com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.linker"/>
\t<sourceEntries>
\t\t<entry name="Core"/>
\t</sourceEntries>
</cproject>
"""


def _values(root, tool, kind):
    option = root.find(f"tool[@superClass='{tool}']/option[@superClass='{tool}.option.{kind}']")
    return [v.get("value") for v in option.findall("listOptionValue")]


def test_both_tools_get_the_define_and_the_selected_library_paths():
    configured = configure(CPROJECT, ("mbf",))
    assert configured.startswith('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
                                 "<?fileVersion 4.0.0?><cproject>")
    root = ET.fromstring(configured.split("?>", 2)[2])
    for tool in COMPILE_TOOLS:
        assert set(DEFINES) <= set(_values(root, tool, "definedsymbols"))
        assert _values(root, tool, "includepaths")[-3:] == [
            '"${workspace_loc:/${ProjName}/test_common}"',
            '"${workspace_loc:/${ProjName}/Unity/src}"',
            '"${workspace_loc:/${ProjName}/lib/mbf}"']
    assert _values(root, COMPILE_TOOLS[1], "definedsymbols") == ["DEBUG", *DEFINES]
    assert [e.get("name") for e in root.iter("entry")] == [
        "Core", "mtk3_bsp2", "Unity/src", "application", "test_common",
        "lib/mbf"]


def test_configuring_twice_changes_nothing():
    once = configure(CPROJECT, ("mbf",))
    assert configure(once, ("mbf",)) == once


def test_switching_application_replaces_the_selected_libraries():
    with_mbf = configure(CPROJECT, ("mbf",))
    without_libraries = configure(with_mbf)
    root = ET.fromstring(without_libraries.split("?>", 2)[2])
    assert [e.get("name") for e in root.iter("entry")] == [
        "Core", "mtk3_bsp2", "Unity/src", "application", "test_common"]
    for tool in COMPILE_TOOLS:
        paths = _values(root, tool, "includepaths")
        assert not any("lib/" in path for path in paths)


def test_model_adds_generated_headers_and_stedgeai_runtime():
    runtime = type("Runtime", (), {
        "include_dir": "/opt/Middlewares/ST/AI/Inc",
        "library_dir": "/opt/Middlewares/ST/AI/Lib/GCC/ARMCortexM33",
        "library": "NetworkRuntime1201_CM33_GCC.a",
    })()
    configured = configure(CPROJECT, ("model",), ("application/generated",), runtime)
    root = ET.fromstring(configured.split("?>", 2)[2])
    assert _values(root, COMPILE_TOOLS[1], "includepaths")[-3:] == [
        '"${workspace_loc:/${ProjName}/lib/model}"',
        '"${workspace_loc:/${ProjName}/application/generated}"',
        '"/opt/Middlewares/ST/AI/Inc"',
    ]
    assert _values(root, LINKER_TOOL, "libraries") == [
        ":NetworkRuntime1201_CM33_GCC.a"]
    assert _values(root, LINKER_TOOL, "directories") == [
        "/opt/Middlewares/ST/AI/Lib/GCC/ARMCortexM33"]
    assert configure(configured, ("model",), ("application/generated",), runtime) == configured
    switched = ET.fromstring(configure(configured).split("?>", 2)[2])
    assert not any("application/generated" in path
                   for path in _values(switched, COMPILE_TOOLS[1], "includepaths"))
    assert _values(switched, LINKER_TOOL, "libraries") == []
    assert _values(switched, LINKER_TOOL, "directories") == []


def test_the_app_folder_is_linked_once():
    project = "<?xml version=\"1.0\"?>\n<projectDescription>\n\t<name>p</name>\n</projectDescription>\n"
    once = link_folder(project, "application", "/repo/board/application")
    assert link_folder(once, "application", "/repo/board/application") == once
    root = ET.fromstring(once.split("?>", 1)[1])
    assert [(l.findtext("name"), l.findtext("type"), l.findtext("location"))
            for l in root.iter("link")] == [("application", "2", "/repo/board/application")]


def test_a_moved_repository_moves_the_link():
    project = "<?xml version=\"1.0\"?>\n<projectDescription>\n\t<name>p</name>\n</projectDescription>\n"
    moved = link_folder(link_folder(project, "application", "/old/board/application"),
                        "application", "/new/board/application")
    root = ET.fromstring(moved.split("?>", 1)[1])
    assert [l.findtext("location") for l in root.iter("link")] == ["/new/board/application"]


def test_a_second_folder_gets_its_own_link():
    project = "<?xml version=\"1.0\"?>\n<projectDescription>\n\t<name>p</name>\n</projectDescription>\n"
    both = link_folder(link_folder(project, "application", "/repo/board/application/rows"),
                       "common", "/repo/board/common")
    root = ET.fromstring(both.split("?>", 1)[1])
    assert [(l.findtext("name"), l.findtext("location")) for l in root.iter("link")] == [
        ("application", "/repo/board/application/rows"), ("common", "/repo/board/common")]


def test_the_app_library_and_test_folders_are_linked():
    project = ("<?xml version=\"1.0\"?>\n<projectDescription>\n\t<name>p</name>\n"
               "\t<linkedResources><link><name>common</name><type>2</type>"
               "<location>/old/common</location></link></linkedResources>\n"
               "</projectDescription>\n")
    once = link_folders(project, "/repo/board/application/rows")
    assert link_folders(once, "/repo/board/application/rows") == once
    root = ET.fromstring(once.split("?>", 1)[1])
    assert [(l.findtext("name"), l.findtext("location")) for l in root.iter("link")] == [
        ("application", "/repo/board/application/rows"), ("lib", LIB),
        ("test_common", TEST_COMMON)]
