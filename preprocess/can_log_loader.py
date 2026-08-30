"""Read a CSV log of CAN frames (timestamp;id;dlc;data) into CanFrame records."""

from datetime import datetime, timezone
from typing import Iterator, NamedTuple

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class CanFrame(NamedTuple):
    timestamp: float   # epoch seconds
    can_id: int
    data: bytes


def _parse_epoch(text: str) -> float:
    # Parsed as UTC so the epoch value does not depend on the machine timezone.
    return datetime.strptime(text, _TIMESTAMP_FORMAT).replace(
        tzinfo=timezone.utc
    ).timestamp()


def load_can_log(path) -> Iterator[CanFrame]:
    with open(path) as f:
        next(f, None)   # skip the header row, which holds column names
        for line in f:
            line = line.strip()
            if not line:
                continue
            fields = line.split(";")
            can_id = int(fields[1], 16)
            dlc = int(fields[2])
            data = bytes(int(b) for b in fields[3:3 + dlc])
            yield CanFrame(_parse_epoch(fields[0]), can_id, data)
