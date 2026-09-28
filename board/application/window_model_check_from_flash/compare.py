"""Compare the board's UART output of this application with ONNX Runtime.

    python3 compare.py UART_LOG

ONNX Runtime gets the same windows of Flash rows, scale and score as the board, read
from the C headers the board was built with, and runs the ONNX file the window model's
C code was generated from.

- The score difference checks the board's window model and scoring against the PC.
- The cycles are the inference time per window.
"""

import argparse
from pathlib import Path
import re

import numpy as np
import onnxruntime

HERE = Path(__file__).resolve().parent
ROWS = HERE.parent / "rule_check_from_flash" / "raw_rows.h"
MODEL = HERE.parent.parent / "lib" / "deployed_window_model"
HEX_WORD = re.compile(r"0x([0-9a-f]{8})\b")
HEX_FLOAT = re.compile(r"-?0x[0-9a-f]\.[0-9a-f]+p[+-]\d+")


def words(text):
    """Float32 values from their 32-bit hexadecimal words."""
    return np.array([int(word, 16) for word in HEX_WORD.findall(text)],
                    dtype=np.uint32).view(np.float32)


def physical_rows():
    """The Flash rows and the number of the first one."""
    text = ROWS.read_text()
    first = int(re.search(r"#define FIRST_ROW (\d+)", text).group(1))
    signals = int(re.search(r"#define RULE_SIGNALS (\d+)", text).group(1))
    rows = words(text[text.index("physical_rows"):]).reshape(-1, signals)
    return first, rows


def config():
    """The rows of a window, and the mean and std the board scales with."""
    text = (MODEL / "window_model_config.h").read_text()
    rows = int(re.search(r"#define WINDOW_MODEL_ROWS (\d+)u", text).group(1))
    arrays = []
    for name in ("window_model_mean", "window_model_std"):
        body = text[text.index(name):]
        body = body[:body.index("}")]
        arrays.append(np.array([float.fromhex(value) for value in HEX_FLOAT.findall(body)],
                               dtype=np.float32))
    return rows, *arrays


def board_output(path):
    """Each window's score and cycles from the UART log, by its last row."""
    scores, cycles = {}, {}
    for line in Path(path).read_text(errors="replace").splitlines():
        found = re.match(r"window at row (\d+) score (0x[0-9a-f]{8}) cycles (\d+)", line)
        if found:
            number = int(found.group(1))
            scores[number] = words(found.group(2))[0]
            cycles[number] = int(found.group(3))
    return scores, cycles


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("uart_log")
    args = parser.parse_args()

    first, physical = physical_rows()
    rows, mean, std = config()
    scaled = (physical - mean) / std
    ends = np.arange(rows - 1, len(scaled))
    windows = scaled[ends[:, None] + np.arange(1 - rows, 1)].reshape(len(ends), -1)
    session = onnxruntime.InferenceSession(str(MODEL / "window_model.onnx"),
                                           providers=["CPUExecutionProvider"])
    reconstructed = session.run(None, {"row": windows})[0]
    signals = physical.shape[1]
    score = ((windows - reconstructed)[:, -signals:] ** 2).mean(axis=1, dtype=np.float32)

    board_scores, cycles = board_output(args.uart_log)
    numbers = [first + end for end in ends]
    missing = [number for number in numbers if number not in board_scores]
    if missing:
        raise SystemExit(f"windows missing from the UART log: {missing}")
    board_score = np.array([board_scores[number] for number in numbers])
    board_cycles = np.array([cycles[number] for number in numbers])

    difference = np.abs(board_score - score)
    print(f"windows: {len(ends)}, ending at rows {numbers[0]} to {numbers[-1]}")
    print(f"score on the PC: {score.min():.4f} to {score.max():.4f}")
    print(f"score, largest absolute difference: {difference.max():.3e}")
    print(f"cycles: mean {board_cycles.mean():.0f}, max {board_cycles.max()}")


if __name__ == "__main__":
    main()
