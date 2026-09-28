"""The rows the PC raises an alarm on for frames the board is sent, as the board runs them.

The applications that print alarms over UART check them against this. It runs the PC
pipeline's own steps. The scale, the threshold and the flagged rows an alarm needs are
read from the C headers the board is built with, so the PC and the board use the same
numbers. The same goes for the window alarm, from the window model's headers.
"""

from pathlib import Path
import re
from typing import NamedTuple

import numpy as np

from common.settings import GridSettings, SplitSettings, TestRunSettings
from detect.alarm import alarmed_rows, k_of_last_n
from models.onnx_files import onnx_residuals
from preprocess.features.grid_sample import resample
from preprocess.features.moving import moving
from preprocess.features.windows import positions, window_ends, window_rows
from rules.hits import hits_of_every_rule

LIB = Path(__file__).resolve().parent / "lib"
TASKS = LIB / "ai_can_anomaly_detection_tasks" / "ai_can_anomaly_detection_tasks.h"
WINDOW_MODEL_DIR = LIB / "deployed_window_model"
STRIDE = LIB / "window_model" / "window_model_stride.h"
HEX_FLOAT = re.compile(r"-?0x[0-9a-f]\.[0-9a-f]+p[+-]\d+")


class WindowAnswer(NamedTuple):
    number: np.ndarray      # the moving rows' numbers, the rows the board scores
    scores: np.ndarray      # the window model's score at each window's last row, else NaN
    threshold: np.float32
    alarm: np.ndarray       # moving rows the window alarm rings on


class Answer(NamedTuple):
    number: np.ndarray      # each row's number, row 1 being 0.1 s after the first frame
    segment: np.ndarray     # which stretch between gaps each row is in
    moving: np.ndarray      # rows above MIN_SPEED, the rows the board scores
    hits: np.ndarray        # moving rows a rule hits
    scores: np.ndarray      # the model's score, NaN where not moving
    threshold: np.float32
    alarm: np.ndarray       # rows the alarm rings on


def scale(model_dir, config="model_config.h", model="instant_model"):
    """The mean and std the board scales with, from `config` of the C model `model`."""
    text = (model_dir / config).read_text()
    arrays = []
    for name in (f"{model}_mean", f"{model}_std"):
        body = text[text.index(name):]
        body = body[:body.index("}")]
        arrays.append(np.array([float.fromhex(value) for value in HEX_FLOAT.findall(body)],
                               dtype=np.float32))
    return arrays


def threshold(model_dir, header="threshold.h"):
    """The threshold the board compares the score with, from `header`."""
    text = (model_dir / header).read_text()
    return np.float32(float.fromhex(HEX_FLOAT.search(text).group(0)))


def defined(path, name):
    """The unsigned integer `#define name` sets in `path`."""
    return int(re.search(rf"#define {name} (0x[0-9A-F]+|\d+)u", path.read_text()).group(1),
               0)


def min_flagged_for_alarm():
    """The k the board raises an alarm at."""
    return defined(TASKS, "MIN_FLAGGED_FOR_ALARM")


def alarm_id():
    """The ID the board reports the alarm with."""
    return defined(TASKS, "ALARM_ID")


def ticks_of(frames):
    """Each tick's number, row and segment for `frames`, timed in seconds since the
    first."""
    grid = GridSettings()
    ticks = list(resample(frames, grid.PERIOD, grid.MAX_HOLD))
    number = np.array([round(t / grid.PERIOD) for t, _ in ticks])
    raw = np.array([row for _, row in ticks], np.float32)
    return number, raw, np.cumsum(np.r_[0, np.diff(number) > 1])


def answer(frames, model_dir):
    """The PC's rows, scores and alarm for `frames`, timed in seconds since the first.

    `model_dir` is the folder under `board/lib/` the board's model is built from. It
    holds `instant_model.onnx`, the float model the C was generated from.
    """
    split, run = SplitSettings(), TestRunSettings()
    number, raw, segment = ticks_of(frames)

    mv = moving(raw, min_speed=split.MIN_SPEED)
    hits = hits_of_every_rule(raw, segment, split.MIN_SPEED)
    mean, std = scale(model_dir)
    scores = np.full(len(raw), np.nan, np.float32)
    scores[mv] = onnx_residuals(str(model_dir / "instant_model.onnx"), (raw[mv] - mean) / std)
    limit = threshold(model_dir)
    alarm = alarmed_rows(scores, limit, hits, segment, run.N, min_flagged_for_alarm())
    return Answer(number, segment, mv, hits, scores, limit, alarm)


def window_answer(frames):
    """The PC's window scores and window alarm for `frames`, timed in seconds since the
    first.

    As on the board, only the moving rows go on, and a gap in their numbers starts the
    windows and the count of flagged rows again. The model is `window_model.onnx` in
    `WINDOW_MODEL_DIR`, the file its C was generated from.
    """
    number, raw, _ = ticks_of(frames)
    mv = moving(raw, min_speed=SplitSettings().MIN_SPEED)
    number, raw = number[mv], raw[mv]
    segment = np.cumsum(np.r_[0, np.diff(number) > 1])
    rows = defined(WINDOW_MODEL_DIR / "window_model_config.h", "WINDOW_MODEL_ROWS")
    stride = defined(STRIDE, "WINDOW_MODEL_STRIDE")
    mean, std = scale(WINDOW_MODEL_DIR, "window_model_config.h", "window_model")
    ends = window_ends(positions(np.ones(len(raw), bool), segment), rows=rows,
                       stride=stride)
    scores = np.full(len(raw), np.nan, np.float32)
    if len(ends):
        windows = window_rows((raw - mean) / std, ends, rows=rows)
        scores[ends] = onnx_residuals(str(WINDOW_MODEL_DIR / "window_model.onnx"),
                                      windows.reshape(len(ends), -1),
                                      signals=raw.shape[1])
    limit = threshold(WINDOW_MODEL_DIR, "window_threshold.h")
    alarm = k_of_last_n(scores > limit, segment, TestRunSettings().N,
                        defined(TASKS, "MIN_FLAGGED_WINDOWS_FOR_ALARM"))
    return WindowAnswer(number, scores, limit, alarm)


def print_alarm_changes(result):
    """Print the rows the alarm starts and ends on, as the board does."""
    print_changes(result.number, result.alarm, alarm_id())


def print_window_alarm_changes(result):
    """Print the rows the window alarm starts and ends on, as the board does."""
    print_changes(result.number, result.alarm, defined(TASKS, "WINDOW_ALARM_ID"))


def print_changes(number, alarm, identifier):
    """Print the rows `alarm` starts and ends on, named by `identifier`."""
    ringing = False
    for row, alarmed in zip(number, alarm):
        if alarmed != ringing:
            print(f"alarm 0x{identifier:08X} {'start' if alarmed else 'end'} at row {row}")
            ringing = alarmed
