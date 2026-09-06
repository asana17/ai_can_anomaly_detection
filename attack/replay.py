"""Replay: replace a window's payloads with ones the bus carried at another time.

The written bytes were observed, so every signal in a replayed message stays inside
its own range and agrees with the others in that message. What breaks is the
agreement with the messages that were not replayed.
"""

from __future__ import annotations

from bisect import bisect_left
from typing import Iterable

from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame


def _by_pgn(frames: list, pgns: set) -> dict:
    """The times and payloads each of `pgns` carried, in order."""
    out = {pgn: ([], []) for pgn in pgns}
    for f in frames:
        pgn = decompose_can_id(f.can_id).pgn
        if pgn in out:
            times, data = out[pgn]
            times.append(f.timestamp)
            data.append(f.data)
    return out


def _nearest(times: list, data: list, t: float):
    """The payload this stream carried closest to `t`, or None if it carried none."""
    if not times:
        return None
    i = min(bisect_left(times, t), len(times) - 1)
    if i and t - times[i - 1] < times[i] - t:
        i -= 1
    return data[i]


def replay(frames: Iterable[CanFrame], pgns, start: float, stop: float,
           source: float) -> list:
    """Give every `pgns` frame in [start, stop] the payload it had `source` seconds on.

    Frame times and counts do not change, so the message rate stays normal and only
    the values move.
    """
    frames = list(frames)
    streams = _by_pgn(frames, set(pgns))
    out = []
    for f in frames:
        pgn = decompose_can_id(f.can_id).pgn
        if pgn in streams and start <= f.timestamp <= stop:
            times, data = streams[pgn]
            payload = _nearest(times, data, source + (f.timestamp - start))
            if payload is not None:
                out.append(CanFrame(f.timestamp, f.can_id, payload))
                continue
        out.append(f)
    return out
