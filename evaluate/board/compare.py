"""Measure what quantizing a run's model to int8 costs.

    python3 -m evaluate.board.compare "data/part_*/*.csv" out runs_clone exported...
"""

from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
import onnxruntime

from assemble.split import split
from board.export import load
from evaluate.counting import detection, scored_set, training_rows
from evaluate.pc.run import Settings, arrays_for, attacks_for, seconds_for
from models.autoencoder import NonlinearAutoencoder, residuals


def rows_for(pattern, out_dir, settings):
    """The calibration rows and the attacked test rows a run scored."""
    logs = sorted(glob.glob(pattern))
    train_logs, test_logs = split(seconds_for(logs, out_dir, settings), settings.TRAIN)
    data, _ = arrays_for(train_logs, out_dir, settings)
    _, calibration = training_rows(data, data["scale"], settings)
    got, _ = attacks_for(train_logs, test_logs, data["scale"], out_dir, settings)
    return calibration, scored_set(got, data["scale"], settings)


def onnx_residuals(path, rows, batch=8192):
    """Each row's mean squared reconstruction error from the ONNX file at `path`."""
    session = onnxruntime.InferenceSession(path, providers=["CPUExecutionProvider"])
    out = []
    for fed in np.array_split(np.asarray(rows, dtype=np.float32),
                              max(len(rows) // batch, 1)):
        got = session.run(None, {"row": fed})[0]
        out.append(((got - fed) ** 2).mean(axis=1))
    return np.concatenate(out)


def models_in(runs_clone, exported):
    """Where an export sits, what it says of itself, and the `k` and `h` it holds."""
    export_dir = os.path.join(runs_clone, "board", exported)
    meta = json.load(open(os.path.join(export_dir, "meta.json")))
    # an export from before several models fitted in one directory names one pair
    listed = meta.get("models") or [{"k": meta["k"], "h": meta["h"]}]
    return export_dir, meta, [(m["k"], m["h"]) for m in listed]


def sources_for(runs_clone, export_dir, run, k, h, signals):
    """The run's model and the int8 ONNX an export quantized from that model."""
    model = NonlinearAutoencoder(signals=signals, latent_dim=k, hidden=h)
    model.load_state_dict(load(os.path.join(runs_clone, run), k, h))
    int8 = os.path.join(export_dir, f"nonlinear_ae_k{k}_h{h}_int8.onnx")
    return {"torch": lambda rows: residuals(rows, model),
            "int8": lambda rows: onnx_residuals(int8, rows)}


def threshold_for(scores, target):
    """The score a run cuts `target` of the calibration rows off at."""
    return float(np.percentile(scores, 100 * (1 - target)))


def main(pattern, out_dir, runs_clone, *exports):
    settings = Settings()
    calibration, test = rows_for(pattern, out_dir, settings)
    scored = int(test["scored"].sum())
    print(f"{len(calibration)} calibration rows, {scored} attacks scored in "
          f"{test['hours']:.1f} hours", flush=True)

    for exported in exports:
        export_dir, meta, models = models_in(runs_clone, exported)
        print(f"\nboard/{exported}, {meta['run']}")
        print(f"{'model':>12}  {'source':>6}  {'threshold':>12}  "
              + "  ".join(f"found in {n}".rjust(11) for n in settings.HOLD)
              + "   " + "  ".join(f"alarms/h {n}".rjust(12) for n in settings.HOLD))
        for k, h in models:
            sources = sources_for(runs_clone, export_dir, meta["run"], k, h,
                                  calibration.shape[1])
            for name, score in sources.items():
                # the model and the int8 ONNX keep a threshold of their own scores
                cut = threshold_for(score(calibration), settings.TARGET)
                cells = detection((score(test["rows"]) > cut) & test["mv"], test,
                                  settings)
                print(f"{f'k={k} h={h}':>12}  {name:>6}  {cut:12.6g}  "
                      + "  ".join(f"{c['found']:>7}/{scored:<3d}" for c in cells)
                      + "   " + "  ".join(f"{c['alarms_per_hour']:12.1f}" for c in cells),
                      flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], *sys.argv[4:])
