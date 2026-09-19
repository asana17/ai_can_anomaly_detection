"""Run the whole comparison over a set of logs and print what each detector catches.

    python3 -m evaluate.pc.run "data/part_*/*.csv" out runs_clone [logs]
"""

from __future__ import annotations

import glob
import os
import sys
import time
from dataclasses import asdict

import numpy as np
import torch

from assemble.split import split
from common.dataset import arrays_for, attacks_for, seconds_for
from common.settings import Settings
from evaluate.counting import detection, scored_set, training_rows
from evaluate.pc.record import begin, record
from models.autoencoder import LinearAutoencoder, NonlinearAutoencoder, fit
from models.autoencoder import residuals as reconstruction_errors
from models.pca import residuals, subspace


def main(pattern, out_dir, runs_clone, files=None):
    settings = Settings()
    run = begin(runs_clone)
    weights = {}
    os.makedirs(out_dir, exist_ok=True)
    logs = sorted(glob.glob(pattern))
    if files:                          # a smoke test asks for fewer
        logs = logs[::max(len(logs) // files, 1)][:files]
    seconds = seconds_for(logs, out_dir, settings)

    train_logs, test_logs = split(seconds, settings.TRAIN)
    print(f"{len(train_logs)} train and {len(test_logs)} test logs, "
          f"{sum(seconds[p] for p in train_logs):.0f}s and "
          f"{sum(seconds[p] for p in test_logs):.0f}s above the minimum speed",
          flush=True)

    clock = time.time()
    data, kept = arrays_for(train_logs, out_dir, settings)
    scale = data["scale"]
    weights["scale.mean"] = torch.from_numpy(scale.mean)
    weights["scale.std"] = torch.from_numpy(scale.std)
    how = "reused" if kept else f"built in {time.time() - clock:.0f}s"
    print(f"grid {how}, train {data['rows'].shape}", flush=True)

    clock = time.time()
    got, kept = attacks_for(train_logs, test_logs, scale, out_dir, settings)
    how = "reused" if kept else f"in {time.time() - clock:.0f}s"
    print(f"attack set {how}, {len(got['attacks'])} attacks", flush=True)

    tr, calibrate = training_rows(data, scale, settings)
    test = scored_set(got, scale, settings)
    rows, mv, quiet, rules = test["rows"], test["mv"], test["quiet"], test["rules"]
    attacks, scored, hours = test["attacks"], test["scored"], test["hours"]
    print(f"moving rows: train {len(tr)}, calibration {len(calibrate)}, "
          f"test {int(test['truth'].sum())}. "
          f"{int(scored.sum())} attacks reach a moving row and moved it")

    passed = quiet & ~rules                 # no attack and no rule, like calibration rows
    print(f"\n{hours:.1f} hours above MIN_SPEED with no attack in them")

    def label(model, k):
        return f"+ {model} k={k}"

    # the first table prints a row as each model is fitted, so the width is set up front
    models = ["pca", "linear ae"] + [f"nonlinear ae h={h}" for h in settings.HIDDEN]
    width = max(len(name) for name in ["detector", "rules"]
                + [label(model, k) for k in settings.COMPONENTS for model in models])

    print(f"\n{'detector':>{width}}  {'threshold':>10}  {'on clean test':>13}  "
          f"{'epochs':>6}")
    detectors = [("rules", np.zeros_like(rules))]
    thresholds = []

    def add(name, calibration_scores, scores, epochs=""):
        cut = np.percentile(calibration_scores, 100 * (1 - settings.TARGET))
        flag = scores > cut
        clean = (flag & passed).sum() / passed.sum()
        print(f"{name:>{width}}  {cut:10.4g}  {clean:13.5f}  {epochs:>6}", flush=True)
        detectors.append((name, flag & mv))
        thresholds.append({"detector": name, "threshold": float(cut),
                           "on_clean_test": float(clean),
                           "epochs": epochs if epochs != "" else None})

    def fitted(model):
        return fit(tr, model, epochs=settings.EPOCHS, batch=settings.BATCH,
                   rate=settings.RATE, threshold=settings.IMPROVEMENT,
                   patience=settings.PATIENCE)

    for k in settings.COMPONENTS:
        space = subspace(tr, k)
        weights[f"pca.k{k}.centre"] = torch.from_numpy(space.centre)
        # safetensors refuses the transposed view subspace returns
        weights[f"pca.k{k}.basis"] = torch.from_numpy(space.basis).contiguous()
        add(label("pca", k), residuals(calibrate, space), residuals(rows, space))
        torch.manual_seed(settings.TORCH_SEED)
        linear = LinearAutoencoder(signals=tr.shape[1], latent_dim=k)
        losses = fitted(linear)
        weights.update({f"linear_ae.k{k}.{n}": t for n, t in linear.state_dict().items()})
        add(label("linear ae", k), reconstruction_errors(calibrate, linear),
            reconstruction_errors(rows, linear), len(losses))
        for h in settings.HIDDEN:
            torch.manual_seed(settings.TORCH_SEED)
            nonlinear = NonlinearAutoencoder(signals=tr.shape[1], latent_dim=k, hidden=h)
            losses = fitted(nonlinear)
            weights.update({f"nonlinear_ae.h{h}.k{k}.{n}": t
                            for n, t in nonlinear.state_dict().items()})
            add(label(f"nonlinear ae h={h}", k),
                reconstruction_errors(calibrate, nonlinear),
                reconstruction_errors(rows, nonlinear), len(losses))

    print(f"\n{'detector':>{width}}   "
          + "  ".join(f"found in {n}".rjust(11) for n in settings.HOLD)
          + "   " + "  ".join(f"alarms/h {n}".rjust(12) for n in settings.HOLD))
    # with a model added, a row is flagged when a rule or the model flags it
    detections = []
    for name, flag in detectors:
        cells = detection(flag, test, settings)
        print(f"{name:>{width}}   "
              + "  ".join(f"{c['found']:>7}/{int(scored.sum()):<3d}" for c in cells)
              + "   " + "  ".join(f"{c['alarms_per_hour']:12.1f}" for c in cells))
        detections.append({"detector": name,
                           "found": {str(c["hold"]): int(c["found"]) for c in cells},
                           "alarms_per_hour": {str(c["hold"]): float(c["alarms_per_hour"])
                                               for c in cells}})

    values = asdict(settings)
    seeds = {name: values.pop(name) for name in ("SEED", "TORCH_SEED")}
    record(run, weights, {
        "seeds": seeds,
        "hyperparameters": {**values, "logs": len(logs)},
        "metrics": {"hours": float(hours), "attacks_scored": int(scored.sum()),
                    "thresholds": thresholds, "detection": detections}})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3],
         int(sys.argv[4]) if len(sys.argv) > 4 else None)
