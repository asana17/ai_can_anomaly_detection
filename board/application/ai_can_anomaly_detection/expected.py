"""Print the rows the alarm starts and ends on when the PC runs one log's frames.

    python3 -m board.application.ai_can_anomaly_detection.expected LOG

LOG is a log of `fetched/frames/frames.parquet`, as `attacked.json` names it.
`fetch.py` downloads both. Row 1
is the row 0.1 s after the first frame, so the rows count from when sending starts.
"""

import argparse
from pathlib import Path

import pyarrow.parquet as pq

from board.pc_answer import LIB, answer, print_alarm_changes
from preprocess.frames.can_log_loader import CanFrame

HERE = Path(__file__).resolve().parent
FRAMES = HERE / "fetched" / "frames" / "frames.parquet"
MODEL_DIR = LIB / "deployed_model"


def frames(log):
    """The log's frames, as the PC sends them."""
    table = pq.read_table(FRAMES, columns=["timestamp", "can_id", "data"],
                          filters=[("log", "=", log)])
    return [CanFrame(time, can_id, data) for time, can_id, data in
            zip(*(table[name].to_pylist() for name in table.column_names))]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log")
    args = parser.parse_args()

    sent = frames(args.log)
    first = sent[0].timestamp
    since_first = [CanFrame(f.timestamp - first, f.can_id, f.data) for f in sent]
    print_alarm_changes(answer(since_first, MODEL_DIR))


if __name__ == "__main__":
    main()
