"""Read a stage's arguments, the same way for every stage."""

from __future__ import annotations

import argparse


def arguments(names, **flags):
    """What the command line holds, keyed by name, for a stage's `main` to take.

    A flag given `False` becomes a switch, anything else an option with that default.
    A flag's `_` is written `-` on the command line.
    The names are the ones `main` takes, so a stage reads them as `main(**arguments(…))`.
    """
    parser = argparse.ArgumentParser()
    for name in names:
        parser.add_argument(name)
    for name, default in flags.items():
        flag = "--" + name.replace("_", "-")
        if default is False:
            parser.add_argument(flag, action="store_true")
        else:
            parser.add_argument(flag, default=default)
    read = parser.parse_args()
    return {name: getattr(read, name) for name in (*names, *flags)}
