"""Export a window of an existing attack set as a board Flash header."""

from __future__ import annotations

import json
import os
import sys

import numpy as np

from preprocess.features.signal_state import SIGNALS

HERE = os.path.dirname(os.path.abspath(__file__))
HEADER = os.path.join(HERE, "application", "rule_check_from_flash", "raw_rows.h")


def window(first, last, total, n):
    """Return an n-row slice centered on an inclusive attack interval."""
    start = min(max((first + last + 1 - n) // 2, 0), total - n)
    return slice(start, start + n)


def bits(rows):
    """Format each float32 value as its exact 32-bit hexadecimal representation."""
    words = np.ascontiguousarray(rows, dtype=np.float32).view(np.uint32)
    return [[f"0x{word:08x}" for word in row] for row in words.tolist()]


def header(raw: np.ndarray, start: int) -> str:
    """C constants for decoded, unscaled physical rows."""
    if raw.ndim != 2 or raw.shape[1] != len(SIGNALS):
        raise ValueError("raw rows must have the signal order and width")
    values = np.asarray(raw, dtype=np.float32)
    lines = ["/* Derived from University of Turku, CAN bus dataset collected from a heavy-duty truck.",
             " * https://doi.org/10.23729/3160254e-85e9-4268-a636-5b3e54091706",
             " * CC BY 4.0: https://creativecommons.org/licenses/by/4.0/",
             " * Modified: replay injection, J1939 decoding, 100 ms sampling, and row selection.",
             f" * board.rule_rows: selected attack-set rows {start} to {start + len(values) - 1}.",
             " */",
             "#ifndef RAW_ROWS_H", "#define RAW_ROWS_H", "#include <stdint.h>", "",
             f"#define RULE_ROWS {len(values)}", f"#define RULE_SIGNALS {len(SIGNALS)}",
             f"#define FIRST_ROW {start}",
             f"#define WHEEL_SPEED_INDEX {SIGNALS.index('wheel_speed')}",
             f"#define CURRENT_GEAR_INDEX {SIGNALS.index('current_gear')}", "",
             "/* Exact float32 bits of the decoded, unscaled physical values. */",
             "static const uint32_t physical_rows[RULE_ROWS][RULE_SIGNALS] = {"]
    lines += ["    {" + ", ".join(row) + "}," for row in bits(values)]
    lines += ["};", "#endif", ""]
    return "\n".join(lines)


def main(out_dir: str, attack_no: int, n: int) -> None:
    if n < 1:
        raise ValueError("row count must be positive")
    with open(os.path.join(out_dir, "injected.json")) as f:
        attacks = json.load(f)
    attack = attacks[attack_no]
    raw = np.load(os.path.join(out_dir, "attacked_raw.npy"), mmap_mode="r")
    if n > len(raw):
        raise ValueError("row count exceeds attack set")
    selected = window(attack["first"], attack["last"], len(raw), n)
    if attack["last"] >= selected.stop or attack["first"] < selected.start:
        raise ValueError("row count is shorter than the selected attack")
    os.makedirs(os.path.dirname(HEADER), exist_ok=True)
    with open(HEADER, "w") as f:
        f.write(header(raw[selected], selected.start))
    print(f"{HEADER}: {n} rows, {n * len(SIGNALS) * 4} Flash bytes for physical rows")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
