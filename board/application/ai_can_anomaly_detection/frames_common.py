"""The frames of the logs sent to the board, and the lines the frames the board sends back
are printed as.

`fetch.py` downloads the frames of every log into `FRAMES`. A log `guidelines/` keeps
has the same columns.
"""

import re
from pathlib import Path

import pyarrow.parquet as pq

from preprocess.frames.can_log_loader import CanFrame

FETCHED = Path(__file__).resolve().parent / "fetched"
FRAMES = FETCHED / "frames" / "frames.parquet"
RECEIVED = re.compile(r"received at ([\d.]+)\s+([0-9A-F]+)\s+\[(\d)\]\s+((?:[0-9A-F]{2} ?)*)")


def frames_of_log(log, source=FRAMES):
    """The frames of `log` in the parquet file `source`, as the PC sends them."""
    table = pq.read_table(source, columns=["timestamp", "can_id", "data"],
                          filters=[("log", "=", log)])
    return [CanFrame(time, can_id, data) for time, can_id, data in
            zip(*(table[name].to_pylist() for name in table.column_names))]


def frame_text(can_id, data):
    """A frame as gs_usb prints it."""
    return "{: >8X}   [{}]  {}".format(can_id, len(data), " ".join(f"{b:02X}" for b in data))


def received_line(seconds, text):
    """The line of a frame the board sent, `text` as `frame_text` gives it, that came at
    `seconds` since the epoch."""
    return f"received at {seconds:.3f} {text}"


def received_frames(lines):
    """Each line `received_line` gave as (seconds it came, ID, data)."""
    for line in lines:
        found = RECEIVED.match(line.strip())
        if found:
            yield (float(found.group(1)), int(found.group(2), 16),
                   bytes.fromhex(found.group(4)))
