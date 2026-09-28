"""The rows the PC raises an alarm on for frames the board is sent, as the board runs them.

The applications that print alarms over UART check them against this. It runs the PC
pipeline's own steps. The scale, the threshold and the flagged rows an alarm needs are
read from the C headers the board is built with, so the PC and the board use the same
numbers.
"""

from pathlib import Path
import re
from typing import NamedTuple

import numpy as np

from common.settings import GridSettings, SplitSettings, TestRunSettings
from detect.alarm import alarmed_rows
from models.onnx_files import onnx_residuals
from preprocess.features.grid_sample import resample
from preprocess.features.moving import moving
from rules.hits import hits_of_every_rule

LIB = Path(__file__).resolve().parent / "lib"
TASKS = LIB / "ai_can_anomaly_detection_tasks" / "ai_can_anomaly_detection_tasks.h"
HEX_FLOAT = re.compile(r"-?0x[0-9a-f]\.[0-9a-f]+p[+-]\d+")


class Answer(NamedTuple):
    number: np.ndarray      # each row's number, row 1 being 0.1 s after the first frame
    segment: np.ndarray     # which stretch between gaps each row is in
    moving: np.ndarray      # rows above MIN_SPEED, the rows the board scores
    hits: np.ndarray        # moving rows a rule hits
    scores: np.ndarray      # the model's score, NaN where not moving
    threshold: np.float32
    alarm: np.ndarray       # rows the alarm rings on


def scale(model_dir):
    """The mean and std the board scales with."""
    text = (model_dir / "model_config.h").read_text()
    arrays = []
    for name in ("instant_model_mean", "instant_model_std"):
        body = text[text.index(name):]
        body = body[:body.index("}")]
        arrays.append(np.array([float.fromhex(value) for value in HEX_FLOAT.findall(body)],
                               dtype=np.float32))
    return arrays


def threshold(model_dir):
    """The threshold the board compares the score with."""
    text = (model_dir / "threshold.h").read_text()
    return np.float32(float.fromhex(HEX_FLOAT.search(text).group(0)))


def min_flagged_for_alarm():
    """The k the board raises an alarm at."""
    return int(re.search(r"#define MIN_FLAGGED_FOR_ALARM (\d+)u", TASKS.read_text()).group(1))


def alarm_id():
    """The ID the board reports the alarm with."""
    return int(re.search(r"#define ALARM_ID (0x[0-9A-F]+)u", TASKS.read_text()).group(1), 16)


def answer(frames, model_dir):
    """The PC's rows, scores and alarm for `frames`, timed in seconds since the first.

    `model_dir` is the folder under `board/lib/` the board's model is built from. It
    holds `instant_model.onnx`, the float model the C was generated from.
    """
    grid, split, run = GridSettings(), SplitSettings(), TestRunSettings()
    ticks = list(resample(frames, grid.PERIOD, grid.MAX_HOLD))
    number = np.array([round(t / grid.PERIOD) for t, _ in ticks])
    raw = np.array([row for _, row in ticks], np.float32)
    segment = np.cumsum(np.r_[0, np.diff(number) > 1])

    mv = moving(raw, min_speed=split.MIN_SPEED)
    hits = hits_of_every_rule(raw, segment, split.MIN_SPEED)
    mean, std = scale(model_dir)
    scores = np.full(len(raw), np.nan, np.float32)
    scores[mv] = onnx_residuals(str(model_dir / "instant_model.onnx"), (raw[mv] - mean) / std)
    limit = threshold(model_dir)
    alarm = alarmed_rows(scores, limit, hits, segment, run.N, min_flagged_for_alarm())
    return Answer(number, segment, mv, hits, scores, limit, alarm)


def print_alarm_changes(result):
    """Print the rows the alarm starts and ends on, as the board does."""
    ringing = False
    for row, alarmed in zip(result.number, result.alarm):
        if alarmed != ringing:
            print(f"alarm 0x{alarm_id():08X} {'start' if alarmed else 'end'} at row {row}")
            ringing = alarmed
