"""Count CAN frames per PGN, and per source address within each PGN."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame


def count_pgns(frames: Iterable[CanFrame]) -> Counter:
    counts: Counter = Counter()
    for frame in frames:
        counts[decompose_can_id(frame.can_id).pgn] += 1
    return counts


def count_pgn_senders(frames: Iterable[CanFrame]) -> dict[int, Counter]:
    senders: dict[int, Counter] = {}
    for frame in frames:
        ident = decompose_can_id(frame.can_id)
        senders.setdefault(ident.pgn, Counter())[ident.source_address] += 1
    return senders
