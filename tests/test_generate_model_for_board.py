import json
import os
import sys

import pytest

from deploy import generate_model_for_board
from deploy.generate_model_for_board import KEPT, generate, models_in

WRITTEN = (*KEPT, "extra.txt")


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
os.makedirs(output)
for name in {WRITTEN!r}:
    with open(os.path.join(output, name), "w") as f:
        f.write(args[args.index("--model") + 1])
""")
    path.chmod(0o755)
    return str(path)


def _entry(k, hidden):
    return {"model": "nonlinear ae", "k": k, "hidden": hidden, "epochs": 1, "batch": 128,
            "rate": 0.001, "improvement": 0.0, "patience": 1, "seed": 0}


def test_every_model_the_export_lists_is_read_in_its_order(tmp_path):
    (tmp_path / "meta.json").write_text(json.dumps(
        {"exported": [_entry(8, 64), _entry(2, 32)]}))
    assert [(m.k, m.hidden) for m in models_in(str(tmp_path))] == [(8, 64), (2, 32)]


def test_only_the_files_named_are_kept(tmp_path):
    dest = tmp_path / "dest"
    generate(_stedgeai(tmp_path), "model.onnx", str(dest))
    assert sorted(os.listdir(dest)) == sorted(KEPT)
    assert (dest / "network.c").read_text() == "model.onnx"


def test_generate_never_overwrites(tmp_path):
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "network.c").write_text("kept")
    with pytest.raises(FileExistsError):
        generate(_stedgeai(tmp_path), "model.onnx", str(dest))
    assert (dest / "network.c").read_text() == "kept"


def test_every_float_file_of_the_export_is_generated(tmp_path, hub):
    models = {"repo": "u/runs", "revision": "abc", "path": "models/t"}
    hub.files = {"onnx/t/meta.json": {"models": models,
                                      "exported": [_entry(8, 64), _entry(2, 32)]}}
    generate_model_for_board.main(_stedgeai(tmp_path), "u/runs", str(tmp_path), "onnx/t")

    path = hub.uploaded[0]["path_in_repo"]
    folder = tmp_path / path
    assert path.startswith("board/")
    assert sorted(os.listdir(folder)) == ["meta.json", "nonlinear_ae_k2_h32",
                                          "nonlinear_ae_k8_h64"]
    assert (folder / "nonlinear_ae_k8_h64" / "network.c").read_text() == str(
        tmp_path / "onnx" / "t" / "nonlinear_ae_k8_h64_float.onnx")
    meta = json.load(open(folder / "meta.json"))
    assert meta["export"] == "onnx/t" and meta["models"] == models
    assert meta["exported"] == [_entry(8, 64), _entry(2, 32)]
