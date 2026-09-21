"""Run the whole comparison over a set of logs and print what each detector catches.

    python3 -m evaluate.pc.run repo revision out runs_repo runs_dir
"""

from __future__ import annotations

import sys
from dataclasses import asdict

import numpy as np
import torch

from common.load_dataset import arrays_from, attacks_from, fetch
from common.settings import Settings
from evaluate.counting import detection, prepare_scoring_input, training_rows
from evaluate.pc.record import end_run, start_run
from models.autoencoder import LinearAutoencoder, NonlinearAutoencoder, fit
from models.autoencoder import residuals as reconstruction_errors
from models.pca import residuals, subspace


def main(repo, revision, out_dir, runs_repo, runs_dir):
    settings = Settings()
    run = start_run(runs_repo, runs_dir)
    weights = {}
    dataset = {"repo": repo, "revision": fetch(repo, revision, out_dir)}

    data = arrays_from(out_dir, settings)
    scale = data["scale"]
    weights["scale.mean"] = torch.from_numpy(scale.mean)
    weights["scale.std"] = torch.from_numpy(scale.std)
    got = attacks_from(out_dir, settings)
    logs = len(got["train_logs"]) + len(got["test_logs"])
    print(f"{len(got['train_logs'])} train and {len(got['test_logs'])} test logs, "
          f"train {data['rows'].shape}, {len(got['attacks'])} attacks", flush=True)

    tr, calibrate = training_rows(data, scale, settings)
    rows_to_score, attacks_to_check = prepare_scoring_input(got, scale, settings)
    rows, mv = rows_to_score["rows"], rows_to_score["mv"]
    quiet, rules, hours = (rows_to_score["quiet"], rows_to_score["rules"],
                           rows_to_score["hours"])
    attacks, scored = attacks_to_check["injected"], attacks_to_check["scorable"]
    print(f"moving rows: train {len(tr)}, calibration {len(calibrate)}, "
          f"test {int(mv.sum())}. "
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
        cells = detection(flag, rows_to_score, attacks_to_check, settings)
        print(f"{name:>{width}}   "
              + "  ".join(f"{c['found']:>7}/{int(scored.sum()):<3d}" for c in cells)
              + "   " + "  ".join(f"{c['alarms_per_hour']:12.1f}" for c in cells))
        detections.append({"detector": name,
                           "found": {str(c["hold"]): int(c["found"]) for c in cells},
                           "alarms_per_hour": {str(c["hold"]): float(c["alarms_per_hour"])
                                               for c in cells}})

    values = asdict(settings)
    seeds = {name: values.pop(name) for name in ("SEED", "TORCH_SEED")}
    end_run(run, weights, {
        "dataset": dataset,
        "seeds": seeds,
        "hyperparameters": {**values, "logs": logs},
        "metrics": {"hours": float(hours), "attacks_scored": int(scored.sum()),
                    "thresholds": thresholds, "detection": detections}})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
