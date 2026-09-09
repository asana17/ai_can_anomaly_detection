"""Read a CSV log of CAN frames (timestamp;id;dlc;data) into CanFrame records."""

from datetime import datetime, timezone
from functools import lru_cache
from typing import Iterator, NamedTuple

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


class CanFrame(NamedTuple):
    timestamp: float   # epoch seconds
    can_id: int
    data: bytes


@lru_cache(maxsize=4096)
def _whole_seconds(date_part: str) -> float:
    # Parsed as UTC so the epoch value does not depend on the machine timezone.
    # Cached because a log holds 50,000 frames and about 60 distinct seconds.
    return datetime.strptime(date_part, _TIMESTAMP_FORMAT).replace(
        tzinfo=timezone.utc
    ).timestamp()


def _parse_epoch(text: str) -> float:
    # The fractional second is optional; some rows are logged to whole seconds.
    date_part, _, frac = text.partition(".")
    seconds = _whole_seconds(date_part)
    if frac:
        seconds += int(frac) / 10 ** len(frac)
    return seconds


def load_can_log(path) -> Iterator[CanFrame]:
    """Yield each row of a CAN log CSV as a CanFrame(timestamp, can_id, data)."""
    with open(path) as f:
        next(f, None)   # skip the header row, which holds column names
        for line in f:
            line = line.strip()
            if not line:
                continue
            fields = line.split(";")
            can_id = int(fields[1], 16)
            dlc = int(fields[2])
            if len(fields) < 3 + dlc:
                continue    # a truncated row would decode as zeros, not as missing
            data = bytes(int(b) for b in fields[3:3 + dlc])
            yield CanFrame(_parse_epoch(fields[0]), can_id, data)
