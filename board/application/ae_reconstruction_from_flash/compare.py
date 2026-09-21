"""Compare the board's UART output of this application with ONNX Runtime.

    python3 compare.py UART_LOG ONNX_FILE

ONNX Runtime gets the same Flash rows, scale and reconstruction error as the board,
read from the C headers the board was built with.

- The reconstruction difference checks the st-ai model alone against ONNX Runtime.
- The reconstruction error difference checks the value the board compares with the
  threshold. It adds the scale and the error computed in C.
- The cycles are the inference time per row.
"""

import argparse
from pathlib import Path
import re

import numpy as np
import onnxruntime

HERE = Path(__file__).resolve().parent
ROWS = HERE.parent / "rule_check_from_flash" / "raw_rows.h"
CONFIG = HERE.parent.parent / "lib" / "active_model" / "model_config.h"
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


def scale():
    """The mean and std the board scales with."""
    text = CONFIG.read_text()
    arrays = []
    for name in ("active_model_mean", "active_model_std"):
        body = text[text.index(name):]
        body = body[:body.index("}")]
        arrays.append(np.array([float.fromhex(value) for value in HEX_FLOAT.findall(body)],
                               dtype=np.float32))
    return arrays


def board_output(path):
    """Each row's reconstruction, reconstruction error and cycles from the UART log."""
    reconstructions, errors, cycles = {}, {}, {}
    for line in Path(path).read_text(errors="replace").splitlines():
        found = re.match(r"row (\d+) reconstruction (.*)", line)
        if found:
            reconstructions[int(found.group(1))] = words(found.group(2))
        found = re.match(r"row (\d+) reconstruction_error (0x[0-9a-f]{8}) cycles (\d+)", line)
        if found:
            number = int(found.group(1))
            errors[number] = words(found.group(2))[0]
            cycles[number] = int(found.group(3))
    return reconstructions, errors, cycles


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("uart_log")
    parser.add_argument("onnx_file")
    args = parser.parse_args()

    first, physical = physical_rows()
    mean, std = scale()
    scaled = (physical - mean) / std
    session = onnxruntime.InferenceSession(args.onnx_file,
                                           providers=["CPUExecutionProvider"])
    reconstructed = session.run(None, {"row": scaled})[0]
    error = ((scaled - reconstructed) ** 2).mean(axis=1, dtype=np.float32)

    board_reconstructions, board_errors, cycles = board_output(args.uart_log)
    numbers = range(first, first + len(physical))
    missing = [number for number in numbers
               if number not in board_reconstructions or number not in board_errors]
    if missing:
        raise SystemExit(f"rows missing from the UART log: {missing}")
    board_reconstruction = np.stack([board_reconstructions[number] for number in numbers])
    board_error = np.array([board_errors[number] for number in numbers])
    board_cycles = np.array([cycles[number] for number in numbers])

    reconstruction_difference = np.abs(board_reconstruction - reconstructed)
    error_difference = np.abs(board_error - error) / error
    print(f"rows: {len(physical)}, from row {first}")
    print(f"reconstruction, largest absolute difference: {reconstruction_difference.max():.3e}")
    print(f"reconstruction error, largest relative difference: {error_difference.max():.3e}")
    print(f"cycles: mean {board_cycles.mean():.0f}, max {board_cycles.max()}")


if __name__ == "__main__":
    main()
