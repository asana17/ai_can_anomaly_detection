"""Write the model the board runs into `board/lib/`, from the runs repository.

    python3 -m board.fetch_model

The C code comes from `BOARD`, the directory `deploy.generate_model_for_board` wrote,
and the scale from the fit that directory records. The threshold comes from
`THRESHOLDS`, which has to be taken on the same fit. All are pinned to `RUNS_REVISION`.
The same model goes into every folder of `DESTINATIONS`, with the float ONNX file the
C code was generated from, which the PC answer runs.
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
RUNS_REVISION = "f324e2e89b9e1c08dfb0681c11fe91b0db4d66e0"
BOARD = "board/20260928-200316"
THRESHOLDS = "thresholds/20260928-114811"
MODEL = "nonlinear_ae_k8_h128"
# the sample applications' model, and the one the entry runs
DESTINATIONS = ("active_model", "deployed_model")


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


def model_config(model, mean, std, board_path, models_path):
    """`model_config.h`, the name of `model` and the scale its rows are z-scored with."""
    name, upper = model.C_NAME, model.C_NAME.upper()
    identifier = f"{model.onnx_name}-float".replace("_", "-")
    return f"""#ifndef {upper}_CONFIG_H
#define {upper}_CONFIG_H

/* {model.onnx_name}_float from {board_path}, with the scale of the fit
 * it came from, {models_path}. */
#define {upper}_ID "{identifier}"

static const float {name}_mean[SIGNAL_COUNT] = {{
{c_array(mean)}
	}};

static const float {name}_std[SIGNAL_COUNT] = {{
{c_array(std)}
	}};

#endif
"""


def threshold_header(threshold, thresholds_path):
    """`threshold.h`, the score above which the model flags a row."""
    return f"""#ifndef BOARD_THRESHOLD_H
#define BOARD_THRESHOLD_H

/* The threshold calibrate took for the model at TARGET, from
 * {thresholds_path}, written as the exact bits of the float32. */
#define THRESHOLD_SCORE {hex_float(threshold)}

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


def main():
    with tempfile.TemporaryDirectory() as fetched:
        board, board_meta = read_dir(RUNS_REPO, BOARD, fetched, RUNS_REVISION)
        models = board_meta["models"]
        onnx = board_meta["onnx"]
        onnx_folder, _ = read_dir(onnx["repo"], onnx["path"], fetched, onnx["revision"])
        thresholds_folder, thresholds_meta = read_dir(RUNS_REPO, THRESHOLDS, fetched,
                                                      RUNS_REVISION)
        if thresholds_meta["models"]["path"] != models["path"]:
            raise ValueError(f"{THRESHOLDS} is taken on "
                             f"{thresholds_meta['models']['path']}, not {models['path']}")
        weights, _ = fetch_fitted_models(models["repo"], models["revision"],
                                         models["path"], fetched)
        with open(os.path.join(thresholds_folder, "thresholds.json")) as f:
            thresholds = json.load(f)
        model = next(model for model in map(model_from, board_meta["exported"])
                     if model.onnx_name == MODEL)
        headers = {
            "model_config.h": model_config(model, weights["scale.mean"].numpy(),
                                           weights["scale.std"].numpy(), BOARD,
                                           models["path"]),
            "threshold.h": threshold_header(threshold_of(thresholds, model), THRESHOLDS)}
        for dest in DESTINATIONS:
            write_model(os.path.join(LIB, dest), os.path.join(board, MODEL),
                        os.path.join(onnx_folder, f"{MODEL}_float.onnx"), model, headers)
            print(f"{MODEL} from {BOARD} written into board/lib/{dest}/", flush=True)


if __name__ == "__main__":
    main()
