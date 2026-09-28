import xml.etree.ElementTree as ET

import pytest

from board.prepare.application import (LIB, MODEL, MODEL_FILES, TEST_COMMON,
                                       application_dir, application_for)
from board.prepare.cli import keep_ioc
from board.prepare.cubeide import (C_COMPILER, C_FLAGS, COMPILE_TOOLS, DEFINES, LINKER_TOOL,
                                   MARKER, MBED_CRYPTO_CONFIG, RELEASE_OPTIMIZATION,
                                   configure, keep_program_in_bank_1, link_folder, link_folders,
                                   start_kernel)
from board.prepare.dependencies import (MBED_CRYPTO_SOURCES, MbedCrypto, mbed_crypto,
                                       stedgeai_runtime)

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


def test_model_application_requires_the_fixed_model_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr("board.prepare.application.LIB", str(tmp_path))
    model = tmp_path / MODEL
    model.mkdir()
    app = tmp_path / "model_check_from_flash"
    with pytest.raises(SystemExit, match="instant_model.c"):
        application_for(str(app))
    for name in MODEL_FILES:
        (model / name).touch()
    selected = application_for(str(app))
    assert selected.libraries == ("mbf", "signals", "scale", "model", "scoring", MODEL)


def test_the_project_ioc_is_kept_in_the_repository(tmp_path, monkeypatch):
    monkeypatch.setattr("board.prepare.cli.CUBEMX", str(tmp_path / "cubemx"))
    project = tmp_path / "project"
    project.mkdir()
    (project / "board.ioc").write_text("Mcu.IP0=RCC\n")
    assert keep_ioc(str(project)) == "copied"
    assert (tmp_path / "cubemx" / "board.ioc").read_text() == "Mcu.IP0=RCC\n"
    assert keep_ioc(str(project)) == "already there"
    (project / "board.ioc").write_text("Mcu.IP0=FDCAN1\n")
    assert keep_ioc(str(project)) == "copied"
    assert (tmp_path / "cubemx" / "board.ioc").read_text() == "Mcu.IP0=FDCAN1\n"


def test_a_project_without_one_ioc_is_an_error(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    with pytest.raises(SystemExit, match="found 0"):
        keep_ioc(str(project))
    (project / "one.ioc").touch()
    (project / "other.ioc").touch()
    with pytest.raises(SystemExit, match="found 2"):
        keep_ioc(str(project))


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


def test_mbed_crypto_requires_its_header_and_sources(tmp_path):
    with pytest.raises(SystemExit):
        mbed_crypto(str(tmp_path))
    (tmp_path / "include/mbedtls").mkdir(parents=True)
    (tmp_path / "include/mbedtls/md.h").touch()
    (tmp_path / "library").mkdir()
    for name in MBED_CRYPTO_SOURCES:
        (tmp_path / "library" / name).touch()
    crypto = mbed_crypto(str(tmp_path))
    assert crypto.include_dir == str(tmp_path / "include")
    assert crypto.sources == tuple(str(tmp_path / "library" / name)
                                   for name in MBED_CRYPTO_SOURCES)


def test_no_marker_is_an_error():
    with pytest.raises(ValueError):
        start_kernel("int main(void)\r\n{\r\n}\r\n")


LINKER_SCRIPT_MEMORY = ("MEMORY\n"
                        "{\n"
                        "  RAM    (xrw)    : ORIGIN = 0x20000000,   LENGTH = 272K\n"
                        "  FLASH    (rx)    : ORIGIN = 0x08000000,   LENGTH = 512K\n"
                        "}\n")


def test_the_program_is_kept_in_bank_1():
    assert keep_program_in_bank_1(LINKER_SCRIPT_MEMORY) == LINKER_SCRIPT_MEMORY.replace(
        "LENGTH = 512K", "LENGTH = 256K")


def test_a_linker_script_without_the_flash_region_is_an_error():
    with pytest.raises(ValueError):
        keep_program_in_bank_1("MEMORY\n{\n}\n")


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


def test_the_c_compiler_gets_the_flags():
    root = ET.fromstring(configure(CPROJECT).split("?>", 2)[2])
    assert _values(root, C_COMPILER, "otherflags") == list(C_FLAGS)


def test_release_is_built_at_o2_and_debug_is_left():
    tool = ('<tool superClass="com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.compiler">'
            '<option superClass="com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.compiler'
            '.option.optimization.level" value="{}"/></tool>')
    cproject = ('<?xml version="1.0"?>\n<cproject>'
                f'<configuration name="Debug">{tool.format("")}</configuration>'
                f'<configuration name="Release">{tool.format("os")}</configuration>'
                '</cproject>\n')
    configured = configure(cproject)
    root = ET.fromstring(configured.split("?>", 1)[1])
    levels = {c.get("name"): _optimization(c) for c in root.iter("configuration")}
    assert levels == {"Debug": "", "Release": RELEASE_OPTIMIZATION}
    assert configure(configured) == configured


def _optimization(configuration):
    option = configuration.find(
        f"tool/option[@superClass='{C_COMPILER}.option.optimization.level']")
    return option.get("value")


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


def test_model_adds_its_headers_and_stedgeai_runtime():
    runtime = type("Runtime", (), {
        "include_dir": "/opt/Middlewares/ST/AI/Inc",
        "library_dir": "/opt/Middlewares/ST/AI/Lib/GCC/ARMCortexM33",
        "library": "NetworkRuntime1201_CM33_GCC.a",
    })()
    configured = configure(CPROJECT, ("model", MODEL), runtime)
    root = ET.fromstring(configured.split("?>", 2)[2])
    assert _values(root, COMPILE_TOOLS[1], "includepaths")[-3:] == [
        '"${workspace_loc:/${ProjName}/lib/model}"',
        '"${workspace_loc:/${ProjName}/lib/active_model}"',
        '"/opt/Middlewares/ST/AI/Inc"',
    ]
    assert _values(root, LINKER_TOOL, "libraries") == [
        ":NetworkRuntime1201_CM33_GCC.a"]
    assert _values(root, LINKER_TOOL, "directories") == [
        "/opt/Middlewares/ST/AI/Lib/GCC/ARMCortexM33"]
    assert configure(configured, ("model", MODEL), runtime) == configured
    switched = ET.fromstring(configure(configured).split("?>", 2)[2])
    assert not any("lib/" in path
                   for path in _values(switched, COMPILE_TOOLS[1], "includepaths"))
    assert _values(switched, LINKER_TOOL, "libraries") == []
    assert _values(switched, LINKER_TOOL, "directories") == []


MBED_CRYPTO = MbedCrypto("/opt/mbed-crypto/include",
                         ("/opt/mbed-crypto/library/md.c", "/opt/mbed-crypto/library/sha256.c"))


def test_mbed_crypto_adds_its_config_headers_and_sources():
    configured = configure(CPROJECT, ("alarm_frames_mac",), None, MBED_CRYPTO)
    root = ET.fromstring(configured.split("?>", 2)[2])
    for tool in COMPILE_TOOLS:
        assert _values(root, tool, "definedsymbols")[-1] == MBED_CRYPTO_CONFIG
        assert _values(root, tool, "includepaths")[-1] == '"/opt/mbed-crypto/include"'
    assert [e.get("name") for e in root.iter("entry")][-2:] == [
        "lib/alarm_frames_mac", "mbed-crypto"]
    assert configure(configured, ("alarm_frames_mac",), None, MBED_CRYPTO) == configured
    switched = ET.fromstring(configure(configured).split("?>", 2)[2])
    for tool in COMPILE_TOOLS:
        assert MBED_CRYPTO_CONFIG not in _values(switched, tool, "definedsymbols")
        assert '"/opt/mbed-crypto/include"' not in _values(switched, tool, "includepaths")
    assert "mbed-crypto" not in [e.get("name") for e in switched.iter("entry")]


def test_mbed_crypto_sources_are_linked_in_a_virtual_folder():
    project = "<?xml version=\"1.0\"?>\n<projectDescription>\n\t<name>p</name>\n</projectDescription>\n"
    once = link_folders(project, "/repo/board/application/rows", MBED_CRYPTO)
    assert link_folders(once, "/repo/board/application/rows", MBED_CRYPTO) == once
    root = ET.fromstring(once.split("?>", 1)[1])
    assert [(l.findtext("name"), l.findtext("type"),
             l.findtext("location") or l.findtext("locationURI"))
            for l in root.iter("link")][-3:] == [
        ("mbed-crypto", "2", "virtual:/virtual"),
        ("mbed-crypto/md.c", "1", "/opt/mbed-crypto/library/md.c"),
        ("mbed-crypto/sha256.c", "1", "/opt/mbed-crypto/library/sha256.c")]
    switched = link_folders(once, "/repo/board/application/rows")
    switched = ET.fromstring(switched.split("?>", 1)[1])
    assert [l.findtext("name") for l in switched.iter("link")] == [
        "application", "lib", "test_common"]


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
