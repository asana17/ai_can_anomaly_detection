"""Replay: replace a window's payloads with ones the bus carried at another time.

The written bytes were observed, so every signal in a replayed PGN stays inside its
own range and agrees with the others in that PGN. What breaks is the agreement with
the PGNs that were not replayed.
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
           source: float, source_log: Iterable[CanFrame] | None = None) -> list:
    """Give every `pgns` frame in [start, stop] the payload it had `source` seconds on.

    Frame times and counts do not change, so the frame rate stays normal and only
    the values move. `source` is a time in `source_log`, the log the payload is taken
    from, which is this one unless another is given.
    """
    frames = list(frames)
    streams = _by_pgn(frames if source_log is None else list(source_log), set(pgns))
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
