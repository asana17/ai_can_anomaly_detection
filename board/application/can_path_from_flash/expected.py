"""Print the rows the alarm and the window alarm start and end on when the PC runs this
application's frames.

    python3 -m board.application.can_path_from_flash.expected

The model is the float ONNX file in `board/lib/active_model/`, the one its C was
generated from. The frames, the scale, the threshold and the flagged rows an alarm
needs are read from the C headers the board is built with. Row 1 is the row 0.1 s after the first frame, as on
the board.
"""

import argparse
from pathlib import Path
import re

from board.pc_answer import (LIB, answer, print_alarm_changes,
                             print_window_alarm_changes, window_answer)
from preprocess.frames.can_log_loader import CanFrame

HERE = Path(__file__).resolve().parent
FRAMES = HERE / "replay_frames.h"
MODEL_DIR = LIB / "active_model"
FRAME = re.compile(r"\{(\d+)u, 0x([0-9a-f]+)u, (\d+)u, \{([^}]*)\}\}")


def frames():
    """The Flash frames, with their times in seconds since the first."""
    for time_us, arb_id, size, data in FRAME.findall(FRAMES.read_text()):
        payload = bytes(int(byte, 16) for byte in data.split(","))
        yield CanFrame(int(time_us) / 1e6, int(arb_id, 16), payload[:int(size)])


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()

    result = answer(frames(), MODEL_DIR)
    number, mv = result.number, result.moving
    print(f"rows: {len(number)}, from row {number[0]} to row {number[-1]}, "
          f"moving {int(mv.sum())}, segments {result.segment[-1] + 1}")
    print(f"rule hits {int(result.hits.sum())}, "
          f"above the threshold {int((result.scores > result.threshold).sum())}")
    print_alarm_changes(result)
    print_window_alarm_changes(window_answer(frames()))


if __name__ == "__main__":
    main()
