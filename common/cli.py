"""Read a stage's arguments, the same way for every stage."""

from __future__ import annotations

import argparse


def arguments(names, **flags):
    """The values of the positional `names`, then of each flag, for a stage's `main`.

    A flag given `False` becomes a switch, anything else an option with that default.
    """
    parser = argparse.ArgumentParser()
    for name in names:
        parser.add_argument(name)
    for name, default in flags.items():
        if default is False:
            parser.add_argument(f"--{name}", action="store_true")
        else:
            parser.add_argument(f"--{name}", default=default)
    read = parser.parse_args()
    return [getattr(read, name) for name in (*names, *flags)]
