from pathlib import Path

from board.flash import commands, project_name


def test_three_commands_prepare_build_and_flash(tmp_path):
    (tmp_path / ".project").write_text(
        "<projectDescription><name>firmware</name></projectDescription>")
    prepare, build, flash = commands(
        tmp_path, Path("/apps/alive"), Path("/workspace"),
        Path("/cubeide"), Path("/programmer"))
    assert prepare[-2:] == [str(tmp_path), "/apps/alive"]
    assert build[-4:] == ["-import", str(tmp_path), "-cleanBuild", "firmware/Debug"]
    assert flash == ["/programmer", "-c", "port=SWD", "-w",
                     str(tmp_path / "Debug/firmware.elf"), "-v", "-rst"]


def test_project_name_comes_from_eclipse_project_file(tmp_path):
    (tmp_path / ".project").write_text(
        "<projectDescription><name>firmware</name></projectDescription>")
    assert project_name(tmp_path) == "firmware"
