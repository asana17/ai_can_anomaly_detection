"""Print what the board's frames say, from what send_test_frames printed.

    python3 -m board.application.ai_can_anomaly_detection.send_test_frames LOG | tee received_frames.txt
    python3 -m board.application.ai_can_anomaly_detection.board_frames received_frames.txt

Only the `received at` lines are read.

Each frame the board sent prints as one line, with its row. An alarm or window alarm
frame prints how many ms after the board made its row it went out. A stored record
frame prints how many ms after the last alarm start it came, and its frame count. A
window backlog frame prints how many ms after the board made its row the window model
finished it, and the rows lost just before it. The time the board made a row is taken
from the last alarm or window alarm frame, less the ms it carries, one row period for
each row between. Each stretch of rows the window model was late on ends with a line
of how many rows it was late on and how many it lost.
"""

import argparse
import re
import sys

from board.pc_answer import TASKS, defined
from common.settings import GridSettings

RECEIVED = re.compile(r"received at ([\d.]+)\s+([0-9A-F]+)\s+\[(\d)\]\s+((?:[0-9A-F]{2} ?)*)")


def little(data, first, size):
    """The unsigned integer in `size` bytes of `data` from `first`, little endian."""
    return int.from_bytes(data[first:first + size], "little")


def frames(lines):
    """Each frame line as (seconds it came, ID, data)."""
    for line in lines:
        found = RECEIVED.match(line.strip())
        if found:
            yield (float(found.group(1)), int(found.group(2), 16),
                   bytes.fromhex(found.group(4)))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("received", help="what send_test_frames printed, - for stdin")
    args = parser.parse_args()

    alarm_id = defined(TASKS, "ALARM_ID")
    window_alarm_id = defined(TASKS, "WINDOW_ALARM_ID")
    backlog_id = defined(TASKS, "WINDOW_BACKLOG_ID")
    stored_id = defined(TASKS, "STORED_RECORD_ID")
    period = GridSettings().PERIOD
    lines = sys.stdin if args.received == "-" else open(args.received)

    made = None          # (row, seconds the board made it) from the last alarm frame
    alarm_started = None  # seconds the last alarm start came
    late = []            # (row, rows lost before it) of the stretch the model is late on

    def end_late():
        if late:
            print(f"rows {late[0][0]} to {late[-1][0]}: window model late on {len(late)} rows, "
                  f"{sum(lost for _, lost in late)} rows lost")
            late.clear()

    for came, can_id, data in frames(lines):
        if can_id != backlog_id:
            end_late()
        if can_id in (alarm_id, window_alarm_id):
            row, ms = little(data, 1, 4), little(data, 5, 2)
            made = (row, came - ms / 1000)
            name = "alarm" if can_id == alarm_id else "window alarm"
            state = "start" if data[0] else "end"
            if can_id == alarm_id and data[0]:
                alarm_started = came
            print(f"row {row}: {name} {state}, {ms} ms after the row was made")
        elif can_id == stored_id:
            row, count = little(data, 0, 4), little(data, 4, 2)
            after = "" if alarm_started is None else \
                f"{round((came - alarm_started) * 1000)} ms after the alarm start, "
            print(f"row {row}: alarm frames stored, {after}{count} frames")
        elif can_id == backlog_id:
            row, lost = little(data, 0, 4), little(data, 4, 2)
            if late and row != late[-1][0] + 1 + lost:
                end_late()
            late.append((row, lost))
            finished = "" if made is None else \
                f", finished {round((came - made[1] - (row - made[0]) * period) * 1000)} ms " \
                "after the row was made"
            print(f"row {row}: window model late{finished}, {lost} rows lost before it")
    end_late()


if __name__ == "__main__":
    main()
