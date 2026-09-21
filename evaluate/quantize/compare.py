"""Measure what quantizing a run's model to int8 costs.

    python3 -m evaluate.quantize.compare repo revision out runs_repo runs_dir exported...
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
from safetensors.torch import load_file

from common.load_dataset import arrays_from, attacks_from, fetch
from common.hub_dirs import download
from common.settings import Settings
from evaluate.counting import detection, prepare_scoring_input, training_rows
from models.autoencoder import NonlinearAutoencoder, residuals
from quantize.export import onnx_residuals, threshold_for


def rows_for(out_dir, settings):
    """The calibration rows and the attacked test rows a run scored."""
    data = arrays_from(out_dir, settings)
    _, calibration = training_rows(data, data["scale"], settings)
    got = attacks_from(out_dir, settings)
    return calibration, prepare_scoring_input(got, data["scale"], settings)


def models_in(export_dir):
    """What an export says of itself, and the `k` and `h` it holds."""
    meta = json.load(open(os.path.join(export_dir, "meta.json")))
    # an export from before several models fitted in one directory names one pair
    listed = meta.get("models") or [{"k": meta["k"], "h": meta["h"]}]
    return meta, [(m["k"], m["h"]) for m in listed]


def _state_of(run_dir, k, h):
    """The `state_dict` of the run's nonlinear autoencoder at `k` and `h`."""
    prefix = f"nonlinear_ae.h{h}.k{k}."
    weights = load_file(os.path.join(run_dir, "weights.safetensors"))
    state = {name[len(prefix):]: tensor for name, tensor in weights.items()
             if name.startswith(prefix)}
    if not state:
        raise ValueError(f"{run_dir} holds no nonlinear autoencoder at k={k} h={h}")
    return state


def sources_for(run_dir, export_dir, k, h, signals):
    """The run's model and the int8 ONNX an export quantized from that model."""
    model = NonlinearAutoencoder(signals=signals, latent_dim=k, hidden=h)
    model.load_state_dict(_state_of(run_dir, k, h))
    int8 = os.path.join(export_dir, f"nonlinear_ae_k{k}_h{h}_int8.onnx")
    return {"torch": lambda rows: residuals(rows, model),
            "int8": lambda rows: onnx_residuals(int8, rows)}


def main(repo, revision, out_dir, runs_repo, runs_dir, *exports):
    settings = Settings()
    fetch(repo, revision, out_dir)
    calibration, (rows_to_score, attacks_to_check) = rows_for(out_dir, settings)
    scored = int(attacks_to_check["scorable"].sum())
    print(f"{len(calibration)} calibration rows, {scored} attacks scored in "
          f"{rows_to_score['hours']:.1f} hours", flush=True)

    for exported in exports:
        export_dir = download(runs_repo, f"quantize/{exported}", runs_dir)
        meta, models = models_in(export_dir)
        run_dir = download(runs_repo, meta["run"], runs_dir)
        print(f"\nquantize/{exported}, {meta['run']}")
        print(f"{'model':>12}  {'source':>6}  {'threshold':>12}  "
              + "  ".join(f"found in {n}".rjust(11) for n in settings.HOLD)
              + "   " + "  ".join(f"alarms/h {n}".rjust(12) for n in settings.HOLD))
        for k, h in models:
            sources = sources_for(run_dir, export_dir, k, h, calibration.shape[1])
            for name, score in sources.items():
                # the model and the int8 ONNX keep a threshold of their own scores
                cut = threshold_for(score(calibration), settings.TARGET)
                flag = (score(rows_to_score["rows"]) > cut) & rows_to_score["mv"]
                cells = detection(flag, rows_to_score, attacks_to_check, settings)
                print(f"{f'k={k} h={h}':>12}  {name:>6}  {cut:12.6g}  "
                      + "  ".join(f"{c['found']:>7}/{scored:<3d}" for c in cells)
                      + "   " + "  ".join(f"{c['alarms_per_hour']:12.1f}" for c in cells),
                      flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], *sys.argv[6:])
