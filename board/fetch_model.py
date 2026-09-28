"""Write the model the board runs into `board/lib/`, from the runs repository.

    python3 -m board.fetch_model

The C code comes from `BOARD`, the directory `deploy.generate_model_for_board` wrote,
and the scale from the fit that directory records. The threshold comes from
`THRESHOLDS`, which has to be taken on the same fit. All are pinned to `RUNS_REVISION`.
The same model goes into every folder of `DESTINATIONS`, with the ONNX file the C code
was generated from, which the PC answer runs.

The window model's C code comes from `WINDOW_BOARD` and goes into
`WINDOW_DESTINATION`, with the scale of its own fit, its rows, and the threshold of
`WINDOW_THRESHOLDS`, taken on the same fit and the same ONNX files as the C code.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile

import numpy as np

from common.hub_dirs import read_dir
from models.fit import fetch_fitted_models
from models.fits import as_dict, model_from

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
RUNS_REPO = "asana17/ai_can_anomaly_detection_runs"
RUNS_REVISION = "22c1127a8d2a9628cd5659364d65da71a6a65c93"
BOARD = "board/20260928-200316"
THRESHOLDS = "thresholds/20260928-114811"
MODEL = "nonlinear_ae_k8_h128"
# the sample applications' model, and the one the entry runs
DESTINATIONS = ("active_model", "deployed_model")
WINDOW_BOARD = "window_board/20260929-070505"
WINDOW_MODEL = "window_delta_ae_r20_s3_k24_h128"
WINDOW_THRESHOLDS = "window_thresholds/20260929-070632"
WINDOW_DESTINATION = "deployed_window_model"
# the header each kind of model's scale goes in
CONFIG_FILES = {"instant_model": "model_config.h", "window_model": "window_model_config.h"}


def code_files(name):
    """The generated files the board builds with, the licence among them."""
    ends = (".c", ".h", "_data.c", "_data.h", "_details.h")
    return [f"{name}{end}" for end in ends] + ["LICENSE.txt"]


def hex_float(value):
    """`value` as a C float literal holding its float32 bits exactly."""
    return float(np.float32(value)).hex() + "f"


def c_array(values):
    """The body of a C float array, two values a line."""
    literals = [hex_float(value) for value in values]
    return "\n".join("\t\t" + ", ".join(literals[at:at + 2]) + ","
                     for at in range(0, len(literals), 2))


def model_config(model, mean, std, precision, board_path, models_path):
    """The config header, the name of `model`, the scale its rows are z-scored with and,
    for a window model, its rows."""
    name, upper = model.C_NAME, model.C_NAME.upper()
    identifier = f"{model.onnx_name}-{precision}".replace("_", "-")
    rows = ""
    if hasattr(model, "rows"):
        rows = f"#define {upper}_ROWS {model.rows}u /* W, the rows of a window */\n\n"
    return f"""#ifndef {upper}_CONFIG_H
#define {upper}_CONFIG_H

/* {model.onnx_name}_{precision} from {board_path}, with the scale of the fit
 * it came from, {models_path}. */
#define {upper}_ID "{identifier}"

{rows}static const float {name}_mean[SIGNAL_COUNT] = {{
{c_array(mean)}
	}};

static const float {name}_std[SIGNAL_COUNT] = {{
{c_array(std)}
	}};

#endif
"""


def threshold_header(threshold, thresholds_path, prefix=""):
    """The threshold header, the score above which the model flags a row. `prefix`
    starts its names, `WINDOW_` for the window model."""
    return f"""#ifndef BOARD_{prefix}THRESHOLD_H
#define BOARD_{prefix}THRESHOLD_H

/* The threshold for the model from {thresholds_path}, written as the
 * exact bits of the float32. */
#define {prefix}THRESHOLD_SCORE {hex_float(threshold)}

#endif
"""


def threshold_of(thresholds, model):
    """The threshold `thresholds.json` gives `model`."""
    wanted = as_dict(model)
    for entry in thresholds:
        if {name: value for name, value in entry.items() if name != "threshold"} == wanted:
            return entry["threshold"]
    raise ValueError(f"no threshold for {model.name}")


def write_model(dest, code, onnx_file, model, headers):
    """Put the generated code of `model` from `code`, the ONNX file it was generated
    from and `headers` into `dest`, in place of the model there."""
    for name in os.listdir(dest):
        os.remove(os.path.join(dest, name))
    for name in code_files(model.C_NAME):
        shutil.copy(os.path.join(code, name), dest)
    shutil.copy(onnx_file, os.path.join(dest, f"{model.C_NAME}.onnx"))
    for name, text in headers.items():
        with open(os.path.join(dest, name), "w") as f:
            f.write(text)


def fetch_board_code(board_path, name, fetched):
    """The folder `board_path` holds, its `meta.json`, the model `name`, the ONNX file its
    C code was generated from, that file's precision, and the weights of its fit."""
    board, board_meta = read_dir(RUNS_REPO, board_path, fetched, RUNS_REVISION)
    models = board_meta["models"]
    source = board_meta.get("quantize", board_meta["onnx"])
    precision = "int8" if "quantize" in board_meta else "float"
    source_folder, _ = read_dir(source["repo"], source["path"], fetched,
                                source["revision"])
    weights, _ = fetch_fitted_models(models["repo"], models["revision"], models["path"],
                                     fetched)
    model = next(model for model in map(model_from, board_meta["exported"])
                 if model.onnx_name == name)
    onnx_file = os.path.join(source_folder, f"{name}_{precision}.onnx")
    return board, board_meta, model, onnx_file, precision, weights


def fetch_threshold(thresholds_path, model, board_meta, fetched):
    """The threshold `thresholds_path` gives `model`. Raises unless it was taken on the
    fit the C code came from and, when on ONNX files, on the files it was generated
    from."""
    folder, meta = read_dir(RUNS_REPO, thresholds_path, fetched, RUNS_REVISION)
    models = board_meta["models"]["path"]
    if meta["models"]["path"] != models:
        raise ValueError(f"{thresholds_path} is taken on {meta['models']['path']}, "
                         f"not {models}")
    source = board_meta.get("quantize", board_meta["onnx"])["path"]
    if meta["onnx_files"] is not None and meta["onnx_files"]["path"] != source:
        raise ValueError(f"{thresholds_path} is taken on {meta['onnx_files']['path']}, "
                         f"not {source}")
    with open(os.path.join(folder, "thresholds.json")) as f:
        return threshold_of(json.load(f), model)


def config_header(model, weights, precision, board_path, board_meta):
    """The config header of `model`, by its file name."""
    return {CONFIG_FILES[model.C_NAME]: model_config(
        model, weights["scale.mean"].numpy(), weights["scale.std"].numpy(), precision,
        board_path, board_meta["models"]["path"])}


def main():
    with tempfile.TemporaryDirectory() as fetched:
        board, board_meta, model, onnx_file, precision, weights = fetch_board_code(
            BOARD, MODEL, fetched)
        headers = {**config_header(model, weights, precision, BOARD, board_meta),
                   "threshold.h": threshold_header(
                       fetch_threshold(THRESHOLDS, model, board_meta, fetched),
                       THRESHOLDS)}
        for dest in DESTINATIONS:
            write_model(os.path.join(LIB, dest), os.path.join(board, MODEL), onnx_file,
                        model, headers)
            print(f"{MODEL} from {BOARD} written into board/lib/{dest}/", flush=True)

        board, board_meta, model, onnx_file, precision, weights = fetch_board_code(
            WINDOW_BOARD, WINDOW_MODEL, fetched)
        dest = os.path.join(LIB, WINDOW_DESTINATION)
        os.makedirs(dest, exist_ok=True)
        headers = {**config_header(model, weights, precision, WINDOW_BOARD, board_meta),
                   "window_threshold.h": threshold_header(
                       fetch_threshold(WINDOW_THRESHOLDS, model, board_meta, fetched),
                       WINDOW_THRESHOLDS, "WINDOW_")}
        write_model(dest, os.path.join(board, WINDOW_MODEL), onnx_file, model, headers)
        print(f"{WINDOW_MODEL} from {WINDOW_BOARD} written into "
              f"board/lib/{WINDOW_DESTINATION}/", flush=True)


if __name__ == "__main__":
    main()
