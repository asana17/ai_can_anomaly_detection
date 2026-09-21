"""Hold-last state: keep the latest payload of each PGN and read a row off them."""

from __future__ import annotations

import math

from preprocess.frames.frame_decode import decode_frame
from preprocess.frames.spn_spec import SPEC

SIGNALS = [d.name for defs in SPEC.values() for d in defs]


class SignalState:
    def __init__(self):
        self._payloads = {}

    def update(self, pgn: int, data: bytes) -> None:
        """Keep `data` as the latest payload of `pgn`, if SPEC decodes that PGN."""
        if pgn in SPEC:
            self._payloads[pgn] = data

    def row(self) -> list:
        """Every signal decoded from its PGN's latest payload, in SIGNALS order.

        A value J1939 reserves, an error or not available, is NaN.
        """
        values = {}
        for pgn, data in self._payloads.items():
            values.update(decode_frame(pgn, data))
        return [values.get(name, math.nan) for name in SIGNALS]

    def ready(self) -> bool:
        """True once every PGN of SPEC has arrived at least once."""
        return len(self._payloads) == len(SPEC)
