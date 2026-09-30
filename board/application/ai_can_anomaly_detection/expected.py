"""Print the rows the alarm and the window alarm start and end on when the PC runs one
log's frames.

    python3 -m board.application.ai_can_anomaly_detection.expected LOG [--frames FRAMES]

LOG is a log of FRAMES, what `fetch.py` downloads unless given, as the `injected.json`
beside it names it. FRAMES can be a log `guidelines/` keeps. Row 1
is the row 0.1 s after the first frame, so the rows count from when sending starts.
"""

import argparse
from pathlib import Path

from board.application.ai_can_anomaly_detection.frames_common import FRAMES, frames_of_log
from board.pc_answer import (LIB, answer, print_alarm_changes,
                             print_window_alarm_changes, window_answer)
from preprocess.frames.can_log_loader import CanFrame

MODEL_DIR = LIB / "deployed_model"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log")
    parser.add_argument("--frames", type=Path, default=FRAMES)
    args = parser.parse_args()

    sent = frames_of_log(args.log, args.frames)
    first = sent[0].timestamp
    since_first = [CanFrame(f.timestamp - first, f.can_id, f.data) for f in sent]
    print_alarm_changes(answer(since_first, MODEL_DIR))
    print_window_alarm_changes(window_answer(since_first))


if __name__ == "__main__":
    main()
