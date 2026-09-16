import json
import os
import sys

import pytest

from quantize.generate import KEPT, generate, models_in

WRITTEN = (*KEPT, "extra.txt")


def _stedgeai(tmp_path):
    """A stand-in for ST Edge AI Core that writes the files `generate` writes."""
    path = tmp_path / "stedgeai"
    path.write_text(f"""#!{sys.executable}
import os, sys
if sys.stdin.readline() != "n\\n":
    sys.exit(1)
args = sys.argv[1:]
output = args[args.index("--output") + 1]
os.makedirs(output)
for name in {WRITTEN!r}:
    with open(os.path.join(output, name), "w") as f:
        f.write(args[args.index("--model") + 1])
""")
    path.chmod(0o755)
    return str(path)


def test_every_model_the_export_lists_is_read_in_its_order(tmp_path):
    (tmp_path / "meta.json").write_text(json.dumps(
        {"models": [{"k": 8, "h": 64, "int8_threshold": 0.1},
                    {"k": 2, "h": 32, "int8_threshold": 0.2}]}))
    assert models_in(str(tmp_path)) == [(8, 64), (2, 32)]


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
