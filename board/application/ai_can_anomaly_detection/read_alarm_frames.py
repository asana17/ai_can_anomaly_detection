"""Print the alarm frames records in a copy of Flash bank 2, oldest first.

    python3 -m board.application.ai_can_anomaly_detection.read_alarm_frames BANK2 [--log LOG]

BANK2 is bank 2 read with the programmer, as the README says. Each record prints the
sector, the sequence, the row alarm A started on and the frame count, then its frames.
With LOG, a log of `fetched/frames/frames.parquet`, it prints instead where the frames
match a run of the log's frames in ID, size and data, or that none does.
"""

import argparse
import struct
from pathlib import Path

from board.application.ai_can_anomaly_detection.expected import frames

SECTOR_BYTES = 8 * 1024
SECTORS = 32
ERASED = 0xFFFFFFFF
HEADER = struct.Struct("<II8x")  # sequence, size of the record after it
HEAD = struct.Struct("<II8x")    # row alarm A started on, frame count
FRAME = struct.Struct("<II8s")   # us since the frame before and size, ID, data
DELTA_MASK = 0xFFFFFF


def records(bank):
    """Each record as (sequence, sector, row, frames), oldest first. A frame is
    (us since the frame before, ID, data cut to its size)."""
    if len(bank) != SECTOR_BYTES * SECTORS:
        raise SystemExit(f"bank 2 is {SECTOR_BYTES * SECTORS} bytes, got {len(bank)}")
    found = []
    for sector in range(SECTORS):
        start = sector * SECTOR_BYTES
        sequence, size = HEADER.unpack_from(bank, start)
        if sequence == ERASED:
            if any(byte != 0xFF for byte in bank[start:start + SECTOR_BYTES]):
                print(f"sector {sector} broken, no header but not erased")
            continue
        row, count = HEAD.unpack_from(bank, start + HEADER.size)
        if size != HEAD.size + count * FRAME.size or HEADER.size + size > SECTOR_BYTES:
            print(f"sector {sector} sequence {sequence} bad size {size} for {count} frames")
            continue
        record_frames = []
        for offset in range(start + HEADER.size + HEAD.size, start + HEADER.size + size,
                            FRAME.size):
            delta_and_size, can_id, data = FRAME.unpack_from(bank, offset)
            record_frames.append((delta_and_size & DELTA_MASK, can_id,
                                  data[:delta_and_size >> 24]))
        found.append((sequence, sector, row, record_frames))
    return sorted(found)


def match(record_frames, sent):
    """The index in sent of the first run that matches record_frames in ID, size and
    data, or None."""
    wanted = [(can_id, data) for _, can_id, data in record_frames]
    keys = [(frame.can_id, bytes(frame.data)) for frame in sent]
    for i in range(len(keys) - len(wanted) + 1):
        if keys[i] == wanted[0] and keys[i:i + len(wanted)] == wanted:
            return i
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bank2")
    parser.add_argument("--log")
    args = parser.parse_args()

    found = records(Path(args.bank2).read_bytes())
    sent = frames(args.log) if args.log else None
    for sequence, sector, row, record_frames in found:
        print(f"sector {sector} sequence {sequence} row {row} frames {len(record_frames)}")
        if sent is None:
            for delta, can_id, data in record_frames:
                print(f"  +{delta:8d} us  {can_id:08X}  [{len(data)}]  {data.hex(' ').upper()}")
            continue
        first = match(record_frames, sent)
        if first is None:
            print("  no run of the log matches")
        else:
            print(f"  matches log frames {first} to {first + len(record_frames) - 1}")


if __name__ == "__main__":
    main()
