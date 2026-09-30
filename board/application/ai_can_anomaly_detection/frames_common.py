"""The frames of the logs sent to the board.

`fetch.py` downloads the frames of every log of the test set `TEST_SET` into `FRAMES`, a
folder of parquet files. A log `guidelines/` keeps is one parquet file with the same
columns.
"""

from pathlib import Path

import pyarrow.parquet as pq

from preprocess.frames.can_log_loader import CanFrame

FETCHED = Path(__file__).resolve().parent / "fetched"
# matched_replay on the test logs of the log split both models were fit on
TEST_SET = "test_sets/20260927-081801"
FRAMES = FETCHED / TEST_SET / "frames"


def frames_of_log(log, source=FRAMES):
    """The frames of `log` in `source`, a parquet file or a folder of them, as the PC sends
    them."""
    table = pq.read_table(source, columns=["timestamp", "can_id", "data"],
                          filters=[("log", "=", log)])
    return [CanFrame(time, can_id, data) for time, can_id, data in
            zip(*(table[name].to_pylist() for name in table.column_names))]
