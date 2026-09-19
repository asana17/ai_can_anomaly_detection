"""Ask git about the code a script runs from."""

from __future__ import annotations

import subprocess


def git(*args):
    """What a git command prints."""
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout
