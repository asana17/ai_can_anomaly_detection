"""Run the whole comparison over a set of logs and print what each detector catches.

    python3 -m evaluate.pc.run "data/part_*/*.csv" out runs_clone [logs]
"""

from __future__ import annotations

import glob
import json
import os
import random
import sys
import time
from dataclasses import asdict, dataclass

import numpy as np
import torch

from assemble.attack_set import attack_set
from assemble.train_set import grid_rows, scale_for
from assemble.grid import MAX_HOLD, PERIOD
from assemble.split import WHEEL, seconds_above, split, split_rows
from evaluate.counting import detection, scored_set, training_rows
from evaluate.pc.record import begin, record
from models.autoencoder import LinearAutoencoder, NonlinearAutoencoder, fit
from models.autoencoder import residuals as reconstruction_errors
from models.pca import residuals, subspace
from preprocess.features.signal_state import SIGNALS


@dataclass(frozen=True)
class Settings:
    """Every value a run is made with, kept together so a run can record all of them."""

    MIN_SPEED: float = 5.0      # km/h, the speed a row has to exceed to be scored
    TRAIN: float = 0.75         # share of the seconds above MIN_SPEED before the test cut
    CALIBRATION: float = 0.10   # share of the training seconds above MIN_SPEED held out
    BLOCK: float = 20.0         # seconds above MIN_SPEED in one calibration window
    GAP: float = 5.0            # seconds of training rows dropped around a calibration row
    DONORS: int = 24            # training logs the replayed payloads are taken from
    SEED: int = 0               # the rng the attacks are drawn with
    COMPONENTS: tuple = (2, 4, 6, 8, 10, 12, 14, 16)
    TARGET: float = 0.001       # share of normal rows the threshold cuts off
    MOVED: float = 1.0          # z distance a replay must push a row by to be an anomaly
    HOLD: tuple = (1, 10)       # rows a flag must persist before it counts as an alarm
    EPOCHS: int = 1000          # the most passes an autoencoder may make over the rows
    BATCH: int = 1024           # training rows in each update of an autoencoder's weights
    RATE: float = 1e-3          # Adam's learning rate
    IMPROVEMENT: float = 1e-4   # share of the best loss an epoch must cut, fit's threshold
    PATIENCE: int = 10          # epochs in a row without that before training stops
    TORCH_SEED: int = 1         # the torch rng each autoencoder is built and trained with
    HIDDEN: tuple = (32, 64, 128)  # hidden units of a nonlinear autoencoder, each reported


def seconds_for(logs, out_dir, settings):
    """The seconds each log spends above the minimum speed, measured once and kept.

    A log's own seconds do not depend on which other logs were asked for, so the file
    is a store of every log ever measured rather than one run's answer. A run over a
    different set measures only the logs missing from it.
    """
    path = os.path.join(out_dir, "seconds.json")
    kept = json.load(open(path)) if os.path.exists(path) else {}
    missing = [p for p in logs if p not in kept]
    if missing:
        kept.update(seconds_above(missing, settings.MIN_SPEED))
        json.dump(kept, open(path, "w"))
    return {p: kept[p] for p in logs}


GRID = ("raw", "t", "seg")
ATTACKED = ("rows", "raw", "t", "seg", "label", "wheel")


def _have(out_dir, names):
    """True once every one of `names` is on disk."""
    return all(os.path.exists(os.path.join(out_dir, n)) for n in names)


def grid_for(train_logs, out_dir):
    """The training logs on the grid, built once and read back on a later run."""
    kept = os.path.join(out_dir, "grid.json")
    shape = {"logs": train_logs, "signals": SIGNALS,
             "period": PERIOD, "max_hold": MAX_HOLD}
    files = [f"grid_{n}.npy" for n in GRID]
    if (os.path.exists(kept) and json.load(open(kept)) == shape
            and _have(out_dir, files)):
        return tuple(np.load(os.path.join(out_dir, f)) for f in files), True
    got = grid_rows(train_logs)
    for name, array in zip(files, got):
        np.save(os.path.join(out_dir, name), array)
    json.dump(shape, open(kept, "w"))
    return got, False


def built_from(train_logs, test_logs, settings):
    """The logs and the settings the attack set was built from."""
    return {"logs": [train_logs, test_logs], "train": settings.TRAIN,
            "donors": settings.DONORS, "calibration": settings.CALIBRATION,
            "block": settings.BLOCK, "gap": settings.GAP, "seed": settings.SEED,
            "signals": SIGNALS, "period": PERIOD, "max_hold": MAX_HOLD}


def arrays_for(train_logs, out_dir, settings):
    """The train and calibration arrays, cut out of the saved grid by time."""
    (raw, times, segments), kept = grid_for(train_logs, out_dir)
    train_rows, calibration_rows = split_rows(raw, times, settings.CALIBRATION,
                                              settings.BLOCK, settings.GAP,
                                              settings.MIN_SPEED)
    moving = raw[:, WHEEL] > settings.MIN_SPEED
    scale = scale_for(raw[train_rows & moving])     # the rows PCA is fitted on
    data = {"scale": scale,
            "rows": scale.apply(raw[train_rows]), "raw": raw[train_rows],
            "t": times[train_rows], "seg": segments[train_rows],
            "calibration_rows": scale.apply(raw[calibration_rows]),
            "calibration_raw": raw[calibration_rows],
            "calibration_t": times[calibration_rows],
            "calibration_seg": segments[calibration_rows]}
    print(f"{int(calibration_rows.sum())} calibration rows in "
          f"{_stretches(calibration_rows)} stretches, the gap drops "
          f"{int((~train_rows & ~calibration_rows).sum())} training rows", flush=True)
    return data, kept


def _stretches(calibration_rows) -> int:
    """How many unbroken runs of calibration rows there are.

    A window a stop interrupts lands in more than one run, so this counts at least as
    many as there are windows.
    """
    return int((calibration_rows
                & ~np.concatenate([[False], calibration_rows[:-1]])).sum())


def attacks_for(train_logs, test_logs, scale, out_dir, settings):
    """The attack set, built once and read back on a later run with the same settings."""
    kept = os.path.join(out_dir, "built.json")
    shape = built_from(train_logs, test_logs, settings)
    files = [f"attacked_{n}.npy" for n in ATTACKED] + ["attacked.json"]
    if (os.path.exists(kept) and json.load(open(kept)) == shape
            and _have(out_dir, files)):
        got = {n: np.load(os.path.join(out_dir, f"attacked_{n}.npy"))
               for n in ATTACKED}
        got["attacks"] = json.load(open(os.path.join(out_dir, "attacked.json")))
        return got, True
    donors = settings.DONORS
    got = attack_set(test_logs, scale, random.Random(settings.SEED),
                     source_logs=train_logs[::max(len(train_logs) // donors, 1)]
                     [:donors])
    for name in ATTACKED:
        np.save(os.path.join(out_dir, f"attacked_{name}.npy"), got[name])
    json.dump(got["attacks"], open(os.path.join(out_dir, "attacked.json"), "w"))
    json.dump(shape, open(kept, "w"))
    return got, False


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
