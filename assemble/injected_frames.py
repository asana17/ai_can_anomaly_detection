"""Write the frames of the attacked test logs to Parquet files."""

from __future__ import annotations

import os

import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA = pa.schema([("log", pa.string()), ("timestamp", pa.float64()),
                    ("can_id", pa.uint32()), ("data", pa.binary()),
                    ("attacked", pa.bool_())])
FRAMES_PER_FILE = 10_000_000                # about 200 logs, and about 40 MB


def _columns(log, frames, hurt):
    """The Parquet columns of one log, its frames after the attack and whether the attack
    changed each of them."""
    return {"log": [log] * len(hurt), "timestamp": [f.timestamp for f in hurt],
            "can_id": [f.can_id for f in hurt], "data": [f.data for f in hurt],
            "attacked": [a.data != b.data for a, b in zip(frames, hurt)]}


def write_and_pass_frames(injected, dest, frames_per_file=FRAMES_PER_FILE):
    """Write the frames of each log `injected` yields to `dest`, and yield the log as it
    came.

    The files are `dest/test-NNNNN.parquet`, each holding about `frames_per_file`
    frames.
    """
    os.makedirs(dest)                       # raises rather than overwrite
    count, batches = 0, []

    def flush():
        nonlocal count, batches
        pq.write_table(pa.Table.from_batches(batches, schema=SCHEMA),
                       os.path.join(dest, f"test-{count:05d}.parquet"))
        count, batches = count + 1, []

    for item in injected:
        path, frames, hurt = item[:3]
        batches.append(pa.RecordBatch.from_pydict(_columns(path, frames, hurt),
                                                  schema=SCHEMA))
        if sum(b.num_rows for b in batches) >= frames_per_file:
            flush()
        yield item
    if batches:
        flush()
