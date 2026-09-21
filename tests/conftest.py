import ctypes
import fnmatch
import json
import os
import subprocess

import numpy as np
import pytest

from common import hf_upload, hub_dirs
from common.schema_validate import check

REVISION = "ab" * 20
COMMIT = "de" * 20
BOARD_RULES = os.path.join(os.path.dirname(__file__), "..", "board", "lib", "rules")


def check_json_files(folder, path_in_repo):
    """Check every JSON file of a directory about to be uploaded against its schema.

    `meta.json` is checked against the schema of the directory's kind, the first part of
    `path_in_repo`, and any other `<name>.json` against `<name>.schema.json`.
    """
    kind = path_in_repo.split("/")[0]
    for name in os.listdir(folder):
        if name == "meta.json":
            check(json.load(open(os.path.join(folder, name))), f"meta.{kind}.schema.json")
        elif name.endswith(".json"):
            check(json.load(open(os.path.join(folder, name))),
                  name.replace(".json", ".schema.json"))


@pytest.fixture
def hub(monkeypatch):
    """Stands in for a Hugging Face repository, logged in.

    `hub.files` maps a path in the repository to the JSON it holds, or to the array a
    `.npy` path holds. Uploads are kept in `hub.uploaded`.
    """
    class Hub:
        files = {}
        uploaded = []

        def whoami(self):
            return {"name": "test"}

        def repo_info(self, repo, repo_type="model"):
            return type("Info", (), {"sha": REVISION})

        def list_repo_files(self, repo, repo_type="model", revision=None):
            return list(Hub.files)

        def upload_folder(self, **kwargs):
            check_json_files(kwargs["folder_path"], kwargs["path_in_repo"])
            Hub.uploaded.append(kwargs)
            return type("Commit", (), {"oid": COMMIT})

    def fetch(name, local_dir):
        path = os.path.join(local_dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if name.endswith(".npy"):
            np.save(path, Hub.files[name])
        else:
            with open(path, "w") as f:
                json.dump(Hub.files[name], f)
        return path

    def hf_hub_download(repo, name, repo_type, revision, local_dir):
        return fetch(name, local_dir)

    def snapshot_download(repo, repo_type, allow_patterns, local_dir, revision=None):
        for name in Hub.files:
            if any(fnmatch.fnmatch(name, p) for p in allow_patterns):
                fetch(name, local_dir)

    monkeypatch.setattr(hub_dirs, "HfApi", Hub)
    monkeypatch.setattr(hf_upload, "HfApi", Hub)
    monkeypatch.setattr(hub_dirs, "hf_hub_download", hf_hub_download)
    monkeypatch.setattr(hub_dirs, "snapshot_download", snapshot_download)
    return Hub


C_TYPES = {"float": ctypes.c_float, "const float *": ctypes.POINTER(ctypes.c_float)}


@pytest.fixture(scope="session")
def board_rule(tmp_path_factory):
    """Build a rule of board/lib/rules for this machine and give its `<name>_hits`.

    The rule is a static inline function in `<name>.h`, so a wrapper `hits` exports it.
    `parameters` are its C parameter types, each a key of C_TYPES.
    """
    def build(name, parameters):
        folder = tmp_path_factory.mktemp(name)
        names = [f"a{i}" for i in range(len(parameters))]
        declared = ", ".join(f"{kind} {a}" for kind, a in zip(parameters, names))
        (folder / "hits.c").write_text(
            f'#include "{name}.h"\n'
            f"bool hits({declared})\n"
            f"{{\n\treturn {name}_hits({', '.join(names)});\n}}\n")
        library = folder / f"{name}.so"
        subprocess.run(["clang", "-shared", "-fPIC", "-Wall", "-Werror", "-I", BOARD_RULES,
                        "-o", library, folder / "hits.c"], check=True)
        function = ctypes.CDLL(str(library)).hits
        function.argtypes = [C_TYPES[kind] for kind in parameters]
        function.restype = ctypes.c_bool
        return function
    return build
