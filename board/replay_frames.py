"""Export the frames behind the Flash rows, attack in, as a board Flash header."""

from __future__ import annotations

import glob
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np

from attack.replay import replay
from board.rule_rows import window
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import load_can_log
from preprocess.frames.spn_spec import SPEC

HERE = os.path.dirname(os.path.abspath(__file__))
HEADER = os.path.join(HERE, "application", "can_path_from_flash", "replay_frames.h")
WARMUP = 1.0  # seconds of frames before the first row, so every PGN has arrived by it


def started(path):
    """When a log starts, as its name gives it, YYYYMMDDhhmmss and microseconds in UTC."""
    name = os.path.splitext(os.path.basename(path))[0]
    return datetime.strptime(name, "%Y%m%d%H%M%S%f").replace(
        tzinfo=timezone.utc).timestamp()


def log_at(paths, time):
    """The log that started last at or before `time`."""
    before = [p for p in paths if started(p) <= time]
    if not before:
        raise ValueError(f"no log starts before {time}")
    return max(before, key=started)


def kept(frames, first, last):
    """The frames from `first` to `last` of the PGNs the board decodes."""
    return [f for f in frames if first <= f.timestamp <= last
            and decompose_can_id(f.can_id).pgn in SPEC]


def header(frames, log, first_row, last_row):
    """C constants for `frames`, their times in microseconds from the first one."""
    origin = frames[0].timestamp
    lines = ["/* Derived from University of Turku, CAN bus dataset collected from a heavy-duty truck.",
             " * https://doi.org/10.23729/3160254e-85e9-4268-a636-5b3e54091706",
             " * CC BY 4.0: https://creativecommons.org/licenses/by/4.0/",
             " * Modified: replay injection and frame selection.",
             f" * board.replay_frames: {os.path.basename(log)}, the frames behind attack-set rows"
             f" {first_row} to {last_row},",
             f" * from {WARMUP:g} s before the first, of the PGNs the board decodes.",
             " */",
             "#ifndef REPLAY_FRAMES_H", "#define REPLAY_FRAMES_H", "#include <stdint.h>", "",
             f"#define REPLAY_FRAMES {len(frames)}", "",
             "typedef struct {",
             "\tuint32_t time_us; /* since the first frame */",
             "\tuint32_t arb_id;",
             "\tuint8_t size;",
             "\tuint8_t data[8];",
             "} ReplayFrame;", "",
             "static const ReplayFrame replay_frames[REPLAY_FRAMES] = {"]
    for f in frames:
        data = ", ".join(f"0x{b:02x}" for b in f.data.ljust(8, b"\0"))
        lines.append(f"    {{{round((f.timestamp - origin) * 1e6)}u, 0x{f.can_id:08x}u,"
                     f" {len(f.data)}u, {{{data}}}}},")
    lines += ["};", "#endif", ""]
    return "\n".join(lines)


def main(out_dir: str, data_dir: str, attack_no: int, n: int) -> None:
    with open(os.path.join(out_dir, "attacked.json")) as f:
        attack = json.load(f)[attack_no]
    t = np.load(os.path.join(out_dir, "attacked_t.npy"), mmap_mode="r")
    rows = window(attack["first"], attack["last"], len(t), n)
    first, last = float(t[rows.start]), float(t[rows.stop - 1])
    paths = glob.glob(os.path.join(data_dir, "part_*", "*.csv"))
    log, donor = log_at(paths, first), log_at(paths, attack["source"])
    frames = replay(list(load_can_log(log)), [attack["pgn"]], attack["start"],
                    attack["stop"], attack["source"], list(load_can_log(donor)))
    frames = kept(frames, first - WARMUP, last)
    arrived = {decompose_can_id(f.can_id).pgn for f in frames if f.timestamp < first}
    if arrived != set(SPEC):
        raise ValueError(f"PGNs {sorted(set(SPEC) - arrived)} miss the warm-up")
    os.makedirs(os.path.dirname(HEADER), exist_ok=True)
    with open(HEADER, "w") as f:
        f.write(header(frames, log, rows.start, rows.stop - 1))
    print(f"{HEADER}: {len(frames)} frames from {os.path.basename(log)},"
          f" donor {os.path.basename(donor)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
