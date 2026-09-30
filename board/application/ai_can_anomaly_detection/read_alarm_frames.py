"""Print the alarm frames records in a copy of Flash bank 2, oldest first.

    python3 -m board.application.ai_can_anomaly_detection.read_alarm_frames BANK2 [--log LOG] [--frames FRAMES]

BANK2 is bank 2 read with the programmer, as the README says. Each record prints the
area, the sequence, the alarm it is for, the row that alarm started on, the frame
count and whether its MAC matches the key in `alarm_frames_mac_demo_key.h`, then its
frames.
With LOG, a log of FRAMES as for `expected.py`, it prints instead where the frames
match a run of the log's frames in ID, size and data, or that none does.
"""

import argparse
import hashlib
import hmac
import re
import struct
from pathlib import Path

from board.application.ai_can_anomaly_detection.frames_common import FRAMES, frames_of_log
from board.pc_answer import LIB, alarm_kind_name, defined

SECTOR_BYTES = 8 * 1024  # FLASH_SECTOR_SIZE of the H533, from the HAL
FLASH_STORE = LIB / "flash_store" / "flash_store.h"
ERASED = 0xFFFFFFFF
HEADER = struct.Struct("<II8x")  # sequence, size of the record after it
HEAD = struct.Struct("<III4x")   # row the alarm started on, frame count, alarm kind
MAC_BYTES = 32                   # HMAC-SHA256 of the head, then the frames
FRAME = struct.Struct("<II8s")   # us since the frame before and size, ID, data
DELTA_MASK = 0xFFFFFF
KEY_FILE = LIB / "alarm_frames_mac" / "alarm_frames_mac_demo_key.h"


def demo_key():
    """The 32 key bytes written in KEY_FILE."""
    body = KEY_FILE.read_text().split("{", 1)[1].split("}", 1)[0]
    key = bytes(int(byte, 16) for byte in re.findall(r"0x([0-9a-fA-F]{2})", body))
    if len(key) != MAC_BYTES:
        raise SystemExit(f"{KEY_FILE} has {len(key)} key bytes, not {MAC_BYTES}")
    return key


def records(bank, key):
    """Each record as (sequence, area, alarm kind, row, MAC matches, frames), oldest
    first. A frame is (us since the frame before, ID, data cut to its size)."""
    area_bytes = defined(FLASH_STORE, "FLASH_STORE_AREA_SECTORS") * SECTOR_BYTES
    if len(bank) == 0 or len(bank) % area_bytes:
        raise SystemExit(f"bank 2 is {len(bank)} bytes, not whole areas of {area_bytes}")
    found = []
    for area in range(len(bank) // area_bytes):
        start = area * area_bytes
        sequence, size = HEADER.unpack_from(bank, start)
        if sequence == ERASED:
            if any(byte != 0xFF for byte in bank[start:start + area_bytes]):
                print(f"area {area} broken, no header but not erased")
            continue
        row, count, alarm = HEAD.unpack_from(bank, start + HEADER.size)
        if (size != HEAD.size + MAC_BYTES + count * FRAME.size or
                HEADER.size + size > area_bytes):
            print(f"area {area} sequence {sequence} bad size {size} for {count} frames")
            continue
        head = start + HEADER.size
        mac = head + HEAD.size
        first_frame = mac + MAC_BYTES
        end = head + size
        expected = hmac.new(key, bank[head:mac] + bank[first_frame:end],
                            hashlib.sha256).digest()
        mac_matches = hmac.compare_digest(expected, bank[mac:first_frame])
        record_frames = []
        for offset in range(first_frame, end, FRAME.size):
            delta_and_size, can_id, data = FRAME.unpack_from(bank, offset)
            record_frames.append((delta_and_size & DELTA_MASK, can_id,
                                  data[:delta_and_size >> 24]))
        found.append((sequence, area, alarm, row, mac_matches, record_frames))
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
    parser.add_argument("--frames", type=Path, default=FRAMES)
    args = parser.parse_args()

    found = records(Path(args.bank2).read_bytes(), demo_key())
    sent = frames_of_log(args.log, args.frames) if args.log else None
    for sequence, area, alarm, row, mac_matches, record_frames in found:
        print(f"area {area} sequence {sequence} {alarm_kind_name(alarm)} row {row} "
              f"frames {len(record_frames)}")
        if mac_matches:
            print("  the MAC matches the one computed with the key")
        else:
            print("  the MAC does not match the one computed with the key")
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
