"""Print the rows the alarm starts and ends on when the PC runs this application's frames.

    python3 -m board.application.can_path_from_flash.expected ONNX_FILE

ONNX_FILE is the float model `board/lib/active_model/` was generated from. The frames,
the scale, the threshold and the flagged rows an alarm needs are read from the C
headers the board is built with. Row 1 is the row 0.1 s after the first frame, as on
the board.
"""

import argparse
from pathlib import Path
import re

import numpy as np
import onnxruntime

from common.settings import GridSettings, SplitSettings, TestRunSettings
from detect.alarm import alarmed_rows
from preprocess.features.grid_sample import resample
from preprocess.features.moving import moving
from preprocess.features.windows import positions
from preprocess.frames.can_log_loader import CanFrame
from rules.hits import rule_hits
from rules.sequence import change_limit, torque_over_load

HERE = Path(__file__).resolve().parent
LIB = HERE.parent.parent / "lib"
FRAMES = HERE / "replay_frames.h"
CONFIG = LIB / "active_model" / "model_config.h"
THRESHOLD = LIB / "active_model" / "threshold.h"
TASKS = LIB / "ai_can_anomaly_detection_tasks" / "ai_can_anomaly_detection_tasks.h"
FRAME = re.compile(r"\{(\d+)u, 0x([0-9a-f]+)u, (\d+)u, \{([^}]*)\}\}")
HEX_FLOAT = re.compile(r"-?0x[0-9a-f]\.[0-9a-f]+p[+-]\d+")


def frames():
    """The Flash frames, with their times in seconds since the first."""
    for time_us, arb_id, size, data in FRAME.findall(FRAMES.read_text()):
        payload = bytes(int(byte, 16) for byte in data.split(","))
        yield CanFrame(int(time_us) / 1e6, int(arb_id, 16), payload[:int(size)])


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


def threshold():
    """The threshold the board compares the score with."""
    return np.float32(float.fromhex(HEX_FLOAT.search(THRESHOLD.read_text()).group(0)))


def min_flagged_for_alarm():
    """The k the board raises an alarm at."""
    return int(re.search(r"#define MIN_FLAGGED_FOR_ALARM (\d+)u", TASKS.read_text()).group(1))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("onnx_file")
    args = parser.parse_args()

    grid, split, run = GridSettings(), SplitSettings(), TestRunSettings()
    ticks = list(resample(frames(), grid.PERIOD, grid.MAX_HOLD))
    number = np.array([round(t / grid.PERIOD) for t, _ in ticks])
    raw = np.array([row for _, row in ticks], np.float32)
    segment = np.cumsum(np.r_[0, np.diff(number) > 1])

    mv = moving(raw, min_speed=split.MIN_SPEED)
    position = positions(mv, segment)
    hits = (rule_hits(raw, split.MIN_SPEED) | change_limit.hits(raw, position)
            | torque_over_load.hits(raw, position)) & mv
    mean, std = scale()
    session = onnxruntime.InferenceSession(args.onnx_file,
                                           providers=["CPUExecutionProvider"])
    scaled = (raw - mean) / std
    reconstructed = session.run(None, {"row": scaled[mv]})[0]
    scores = np.full(len(raw), np.nan, np.float32)
    scores[mv] = ((scaled[mv] - reconstructed) ** 2).mean(axis=1, dtype=np.float32)
    alarm = alarmed_rows(scores, threshold(), hits, segment, run.N, min_flagged_for_alarm())

    print(f"rows: {len(raw)}, from row {number[0]} to row {number[-1]}, "
          f"moving {int(mv.sum())}, segments {segment[-1] + 1}")
    print(f"rule hits {int(hits.sum())}, above the threshold {int((scores > threshold()).sum())}")
    ringing = False
    for row, alarmed in zip(number, alarm):
        if alarmed != ringing:
            print(f"alarm {'start' if alarmed else 'end'} at row {row}")
            ringing = alarmed


if __name__ == "__main__":
    main()
