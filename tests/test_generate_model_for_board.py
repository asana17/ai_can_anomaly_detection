import json
import os
import sys

import pytest

from deploy import generate_model_for_board
from deploy.generate_model_for_board import TARGET, generate, kept_files

REVISION = "ab" * 20
COMMIT = "de" * 20


def _stedgeai(tmp_path):
    """A stand-in for ST Edge AI Core that writes the files `generate` writes."""
    path = tmp_path / "stedgeai"
    path.write_text(f"""#!{sys.executable}
import os, sys
args = sys.argv[1:]
if args == ["--version"]:
    print("ST Edge AI Core v0.0.0")
    sys.exit(0)
if sys.stdin.readline() != "n\\n":
    sys.exit(1)
output = args[args.index("--output") + 1]
name = args[args.index("--name") + 1]
os.makedirs(output)
for written in (name + ".c", name + ".h", name + "_data.c", name + "_data.h",
                name + "_details.h", name + "_c_info.json",
                name + "_generate_report.txt", "LICENSE.txt", "extra.txt"):
    with open(os.path.join(output, written), "w") as f:
        f.write(args[args.index("--model") + 1])
""")
    path.chmod(0o755)
    return str(path)


def _entry(k, hidden):
    return {"model": "nonlinear ae", "k": k, "hidden": hidden, "epochs": 1, "batch": 128,
            "rate": 0.001, "improvement": 0.0, "patience": 1, "seed": 0}


def test_only_the_files_named_are_kept(tmp_path):
    dest = tmp_path / "dest"
    generate(_stedgeai(tmp_path), "model.onnx", "some_model", str(dest))
    assert sorted(os.listdir(dest)) == sorted(kept_files("some_model"))
    assert (dest / "some_model.c").read_text() == "model.onnx"


def test_generate_never_overwrites(tmp_path):
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "some_model.c").write_text("kept")
    with pytest.raises(FileExistsError):
        generate(_stedgeai(tmp_path), "model.onnx", "some_model", str(dest))
    assert (dest / "some_model.c").read_text() == "kept"


def test_every_float_file_of_the_export_is_generated(tmp_path, hub):
    models = {"repo": "u/runs", "revision": REVISION, "path": "models/20260101-000000"}
    hub.files = {"onnx/20260101-000000/meta.json": {
        "models": models, "exported": [_entry(8, 64), _entry(2, 32)]}}
    made = generate_model_for_board.main(_stedgeai(tmp_path), "u/runs", COMMIT,
                                         "onnx/20260101-000000", str(tmp_path))

    folder = tmp_path / made["path"]
    assert made["path"].startswith("board/")
    assert sorted(os.listdir(folder)) == ["meta.json", "nonlinear_ae_k2_h32",
                                          "nonlinear_ae_k8_h64"]
    assert (folder / "nonlinear_ae_k8_h64" / "instant_model.c").read_text() == str(
        tmp_path / "onnx" / "20260101-000000" / "nonlinear_ae_k8_h64_float.onnx")
    meta = json.load(open(folder / "meta.json"))
    assert meta["onnx"] == {"repo": "u/runs", "revision": COMMIT,
                            "path": "onnx/20260101-000000"}
    assert meta["inputs"] == {"onnx": "onnx/20260101-000000", "target": TARGET}
    assert meta["models"] == models
    assert meta["exported"] == [_entry(8, 64), _entry(2, 32)]


def test_a_window_export_is_generated_as_the_window_model(tmp_path, hub):
    models = {"repo": "u/runs", "revision": REVISION,
              "path": "window_models/20260101-000000"}
    window = {**_entry(4, 8), "model": "window nonlinear ae", "rows": 3}
    hub.files = {"window_onnx/20260101-000000/meta.json": {
        "models": models, "exported": [window]}}
    made = generate_model_for_board.main(_stedgeai(tmp_path), "u/runs", COMMIT,
                                         "window_onnx/20260101-000000", str(tmp_path))
    assert made["path"].startswith("window_board/")

    generated = tmp_path / made["path"] / "window_nonlinear_ae_r3_k4_h8"
    assert sorted(os.listdir(generated)) == sorted(kept_files("window_model"))
    assert (generated / "window_model.c").read_text() == str(
        tmp_path / "window_onnx" / "20260101-000000"
        / "window_nonlinear_ae_r3_k4_h8_float.onnx")
    assert json.load(open(tmp_path / made["path"] / "meta.json"))["inputs"] == {
        "onnx": "window_onnx/20260101-000000", "target": TARGET}
