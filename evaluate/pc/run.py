"""Run the whole comparison over a set of logs and print what each detector catches.

    python3 -m evaluate.pc.run "data/part_*/*.csv" out [logs]
"""

from __future__ import annotations

import glob
import json
import os
import random
import sys
import time
from functools import partial

import numpy as np
import torch

from assemble.attack_set import attack_set
from assemble.train_set import grid_rows, scale_for
from assemble.grid import MAX_HOLD, PERIOD
from assemble.split import WHEEL, seconds_above, split, split_rows
from models.autoencoder import LinearAutoencoder, NonlinearAutoencoder, fit
from models.autoencoder import residuals as reconstruction_errors
from models.pca import residuals, subspace
from preprocess.features.signal_state import SIGNALS
from rules.instant import (engine_off, gear_ratio, pedal_conflict, range_check,
                           reverse_speed, shaft_ratio, speed_agreement, steering_sign,
                           stopped_shaft)

MIN_SPEED = 5.0         # km/h, the speed a row has to exceed to be scored
TRAIN = 0.75            # share of the seconds above MIN_SPEED before the test cut
CALIBRATION = 0.10      # share of the training seconds above MIN_SPEED held out
BLOCK = 20.0            # seconds above MIN_SPEED in one calibration window
GAP = 5.0               # seconds of training rows dropped around a calibration row
DONORS = 24             # training logs the replayed payloads are taken from
SEED = 0                # the rng the attacks are drawn with
COMPONENTS = (2, 4, 6, 8, 10, 12, 14, 16)
TARGET = 0.001          # share of normal rows the threshold cuts off
MOVED = 1.0             # z distance a replay must push a row by to be an anomaly
HOLD = (1, 10)          # rows a flag must persist before it counts as an alarm
EPOCHS = 500            # the most passes an autoencoder may make over the training rows
BATCH = 1024            # training rows in each update of an autoencoder's weights
RATE = 1e-3             # Adam's learning rate
IMPROVEMENT = 1e-4      # share of the best loss an epoch must cut, fit's threshold
PATIENCE = 10           # epochs in a row without that before training stops
TORCH_SEED = 0          # the torch rng each autoencoder is built and trained with
HIDDEN = (32, 64, 128)  # hidden units of a nonlinear autoencoder, each one reported
INSTANT = (range_check.violations, speed_agreement.violations,
           partial(shaft_ratio.violations, min_speed=MIN_SPEED),
           partial(gear_ratio.violations, min_speed=MIN_SPEED),
           partial(steering_sign.violations, min_speed=MIN_SPEED),
           engine_off.violations, pedal_conflict.violations,
           stopped_shaft.violations, reverse_speed.violations)


def seconds_for(logs, out_dir):
    """The seconds each log spends above the minimum speed, measured once and kept.

    A log's own seconds do not depend on which other logs were asked for, so the file
    is a store of every log ever measured rather than one run's answer. A run over a
    different set measures only the logs missing from it.
    """
    path = os.path.join(out_dir, "seconds.json")
    kept = json.load(open(path)) if os.path.exists(path) else {}
    missing = [p for p in logs if p not in kept]
    if missing:
        kept.update(seconds_above(missing, MIN_SPEED))
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


def built_from(train_logs, test_logs):
    """The logs and the settings the attack set was built from."""
    return {"logs": [train_logs, test_logs], "train": TRAIN, "donors": DONORS,
            "calibration": CALIBRATION, "block": BLOCK, "gap": GAP,
            "seed": SEED, "signals": SIGNALS,
            "period": PERIOD, "max_hold": MAX_HOLD}


def arrays_for(train_logs, out_dir):
    """The train and calibration arrays, cut out of the saved grid by time."""
    (raw, times, segments), kept = grid_for(train_logs, out_dir)
    train_rows, calibration_rows = split_rows(raw, times, CALIBRATION, BLOCK, GAP,
                                              MIN_SPEED)
    moving = raw[:, WHEEL] > MIN_SPEED
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


def attacks_for(train_logs, test_logs, scale, out_dir):
    """The attack set, built once and read back on a later run with the same settings."""
    kept = os.path.join(out_dir, "built.json")
    shape = built_from(train_logs, test_logs)
    files = [f"attacked_{n}.npy" for n in ATTACKED] + ["attacked.json"]
    if (os.path.exists(kept) and json.load(open(kept)) == shape
            and _have(out_dir, files)):
        got = {n: np.load(os.path.join(out_dir, f"attacked_{n}.npy"))
               for n in ATTACKED}
        got["attacks"] = json.load(open(os.path.join(out_dir, "attacked.json")))
        return got, True
    got = attack_set(test_logs, scale, random.Random(SEED),
                     source_logs=train_logs[::max(len(train_logs) // DONORS, 1)]
                     [:DONORS])
    for name in ATTACKED:
        np.save(os.path.join(out_dir, f"attacked_{name}.npy"), got[name])
    json.dump(got["attacks"], open(os.path.join(out_dir, "attacked.json"), "w"))
    json.dump(shape, open(kept, "w"))
    return got, False


def rule_hits(raw):
    """True where an instant rule fires, read off physical values rather than scaled ones."""
    return np.array([any(check(dict(zip(SIGNALS, row))) for check in INSTANT)
                     for row in raw.tolist()], dtype=bool)


def found(flags, attacks, pick):
    """How many of the picked attacks have a flagged row."""
    return sum(flags[a["first"]:a["last"] + 1].any()
               for a, keep in zip(attacks, pick) if keep)


def touched(flags, attacks):
    """For each attack, whether any of its rows is flagged."""
    return np.array([flags[a["first"]:a["last"] + 1].any() for a in attacks], dtype=bool)


def persistent(flag, segment, need):
    """True where `need` rows in a row are flagged, without crossing a segment."""
    if need <= 1:
        return flag
    out, run = np.zeros(len(flag), bool), 0
    for i in range(len(flag)):
        run = run + 1 if flag[i] and i and segment[i] == segment[i - 1] else int(flag[i])
        out[i] = run >= need
    return out


def alarms(flag):
    """How many separate stretches of flagged rows there are."""
    return int((flag & ~np.concatenate([[False], flag[:-1]])).sum())


def period_of(times):
    """The grid period, taken from the commonest step between rows."""
    steps = np.diff(times)
    return float(np.median(steps[steps > 0]))


def main(pattern, out_dir, files=None):
    os.makedirs(out_dir, exist_ok=True)
    logs = sorted(glob.glob(pattern))
    if files:                          # a smoke test asks for fewer
        logs = logs[::max(len(logs) // files, 1)][:files]
    seconds = seconds_for(logs, out_dir)

    train_logs, test_logs = split(seconds, TRAIN)
    print(f"{len(train_logs)} train and {len(test_logs)} test logs, "
          f"{sum(seconds[p] for p in train_logs):.0f}s and "
          f"{sum(seconds[p] for p in test_logs):.0f}s above the minimum speed",
          flush=True)

    clock = time.time()
    data, kept = arrays_for(train_logs, out_dir)
    scale = data["scale"]
    how = "reused" if kept else f"built in {time.time() - clock:.0f}s"
    print(f"grid {how}, train {data['rows'].shape}", flush=True)

    clock = time.time()
    got, kept = attacks_for(train_logs, test_logs, scale, out_dir)
    how = "reused" if kept else f"in {time.time() - clock:.0f}s"
    print(f"attack set {how}, {len(got['attacks'])} attacks", flush=True)

    def moving(rows):
        return scale.undo(rows)[:, WHEEL] > MIN_SPEED

    clean = ~rule_hits(data["calibration_raw"])
    tr = data["rows"][moving(data["rows"])]
    calibrate = data["calibration_rows"][moving(data["calibration_rows"]) & clean]
    rows, label = got["rows"], got["label"]
    mv = moving(rows)                       # what a detector reads, attack included
    truth = got["wheel"] > MIN_SPEED        # what is scored, the speed before the attack
    quiet = truth & ~label
    attacks = got["attacks"]
    reach = touched(truth, attacks)
    moved = np.array([a["moved"] for a in attacks])
    scored = reach & (moved >= MOVED)
    print(f"moving rows: train {len(tr)}, calibration {len(calibrate)}, "
          f"test {int(truth.sum())}. "
          f"{int(scored.sum())} attacks reach a moving row and moved it")

    rules = rule_hits(got["raw"]) & mv
    passed = quiet & ~rules                 # no attack and no rule, like calibration rows
    hours = quiet.sum() * period_of(got["t"]) / 3600
    print(f"\n{hours:.1f} hours above MIN_SPEED with no attack in them")

    def label(model, k):
        return f"+ {model} k={k}"

    # the first table prints a row as each model is fitted, so the width is set up front
    models = ["pca", "linear ae"] + [f"nonlinear ae h={h}" for h in HIDDEN]
    width = max(len(name) for name in ["detector", "rules"]
                + [label(model, k) for k in COMPONENTS for model in models])

    print(f"\n{'detector':>{width}}  {'threshold':>10}  {'on clean test':>13}  "
          f"{'epochs':>6}")
    detectors = [("rules", np.zeros_like(rules))]

    def add(name, calibration_scores, scores, epochs=""):
        cut = np.percentile(calibration_scores, 100 * (1 - TARGET))
        flag = scores > cut
        print(f"{name:>{width}}  {cut:10.4g}  "
              f"{(flag & passed).sum() / passed.sum():13.5f}  {epochs:>6}", flush=True)
        detectors.append((name, flag & mv))

    for k in COMPONENTS:
        space = subspace(tr, k)
        add(label("pca", k), residuals(calibrate, space), residuals(rows, space))
        torch.manual_seed(TORCH_SEED)
        linear = LinearAutoencoder(signals=tr.shape[1], latent_dim=k)
        losses = fit(tr, linear, epochs=EPOCHS, batch=BATCH, rate=RATE,
                     threshold=IMPROVEMENT, patience=PATIENCE)
        add(label("linear ae", k), reconstruction_errors(calibrate, linear),
            reconstruction_errors(rows, linear), len(losses))
        for h in HIDDEN:
            torch.manual_seed(TORCH_SEED)
            nonlinear = NonlinearAutoencoder(signals=tr.shape[1], latent_dim=k, hidden=h)
            losses = fit(tr, nonlinear, epochs=EPOCHS, batch=BATCH, rate=RATE,
                         threshold=IMPROVEMENT, patience=PATIENCE)
            add(label(f"nonlinear ae h={h}", k),
                reconstruction_errors(calibrate, nonlinear),
                reconstruction_errors(rows, nonlinear), len(losses))

    print(f"\n{'detector':>{width}}   "
          + "  ".join(f"found in {n}".rjust(11) for n in HOLD)
          + "   " + "  ".join(f"alarms/h {n}".rjust(12) for n in HOLD))
    # with a model added, a row is flagged when a rule or the model flags it
    for name, flag in detectors:
        cells = []
        for need in HOLD:
            on = persistent(rules | flag, got["seg"], need)
            cells.append((found(on, attacks, scored), alarms(on & quiet) / hours))
        print(f"{name:>{width}}   "
              + "  ".join(f"{c:>7}/{int(scored.sum()):<3d}" for c, _ in cells)
              + "   " + "  ".join(f"{a:12.1f}" for _, a in cells))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
