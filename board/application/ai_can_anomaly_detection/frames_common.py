"""The frames of the logs sent to the board.

`fetch.py` downloads the frames of every log into `FRAMES`. A log `guidelines/` keeps
has the same columns.
"""

from pathlib import Path

import pyarrow.parquet as pq

from preprocess.frames.can_log_loader import CanFrame

FETCHED = Path(__file__).resolve().parent / "fetched"
FRAMES = FETCHED / "frames" / "frames.parquet"


def frames_of_log(log, source=FRAMES):
    """The frames of `log` in the parquet file `source`, as the PC sends them."""
    table = pq.read_table(source, columns=["timestamp", "can_id", "data"],
                          filters=[("log", "=", log)])
    return [CanFrame(time, can_id, data) for time, can_id, data in
            zip(*(table[name].to_pylist() for name in table.column_names))]
