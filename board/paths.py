"""Where the board tools find things on this machine, from the untracked `board/paths.json`."""

import json
from pathlib import Path

PATHS = Path(__file__).resolve().parent / "paths.json"


def read_paths(*names):
    """The entries `names` of `board/paths.json`, each with `~` expanded."""
    if not PATHS.is_file():
        raise SystemExit(f"no {PATHS}")
    entries = json.loads(PATHS.read_text())
    missing = [name for name in names if name not in entries]
    if missing:
        raise SystemExit(f"{PATHS} lacks " + ", ".join(missing))
    return tuple(Path(entries[name]).expanduser() for name in names)
