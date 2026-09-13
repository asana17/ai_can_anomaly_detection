"""Run the whole comparison over a set of logs and print what each detector catches.

    python3 -m evaluate.run "data/part_*/*.csv" out [logs]
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

from assemble.attack_set import attack_set
from assemble.train_set import grid_rows, scale_for
from assemble.grid import MAX_HOLD, PERIOD
from assemble.split import WHEEL, seconds_above, split, split_rows
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
BANDS = ((1.0, 2.0), (2.0, 4.0), (4.0, np.inf))
HOLD = (1, 10)          # rows a flag must persist before it counts as an alarm
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
ATTACKED = ("rows", "raw", "t", "seg", "label")


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
    scale = scale_for(raw[train_rows])      # the fit never sees a calibration row
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
    mv = moving(rows)
    quiet = mv & ~label
    attacks = got["attacks"]
    reach = touched(mv, attacks)
    moved = np.array([a["moved"] for a in attacks])
    scored = reach & (moved >= BANDS[0][0])
    print(f"moving rows: train {len(tr)}, calibration {len(calibrate)}, "
          f"test {int(mv.sum())}. "
          f"{int(scored.sum())} attacks reach a moving row and moved it")

    rules = rule_hits(got["raw"]) & mv
    passed = quiet & ~rules                 # no attack and no rule, like calibration rows
    hours = quiet.sum() * period_of(got["t"]) / 3600
    print(f"\n{hours:.1f} hours above MIN_SPEED with no attack in them")

    print(f"\n{'k':>4}  {'threshold':>10}  {'on clean test':>13}")
    detectors = [("rules", np.zeros_like(rules))]
    for k in COMPONENTS:
        space = subspace(tr, k)
        cut = np.percentile(residuals(calibrate, space), 100 * (1 - TARGET))
        flag = residuals(rows, space) > cut
        print(f"{k:>4}  {cut:10.4f}  {(flag & passed).sum() / passed.sum():13.5f}",
              flush=True)
        detectors.append((f"+ pca k={k}", flag & mv))

    print(f"\n{'detector':>11}   " + "  ".join(f"found in {n}".rjust(11) for n in HOLD)
          + "   " + "  ".join(f"alarms/h {n}".rjust(12) for n in HOLD))
    # with PCA added, a row is flagged when a rule or PCA flags it
    for name, flag in detectors:
        cells = []
        for need in HOLD:
            on = persistent(rules | flag, got["seg"], need)
            cells.append((found(on, attacks, scored), alarms(on & quiet) / hours))
        print(f"{name:>11}   "
              + "  ".join(f"{c:>7}/{int(scored.sum()):<3d}" for c, _ in cells)
              + "   " + "  ".join(f"{a:12.1f}" for _, a in cells))

    print(f"\nwhat the rules leave the models, at {HOLD[-1]} rows held")
    caught = persistent(rules & mv, got["seg"], HOLD[-1])
    left = scored & ~touched(caught, attacks)
    print(f"  rules leave {int(left.sum())} of {int(scored.sum())} attacks")
    for lo, hi in BANDS:
        pick = left & (moved >= lo) & (moved < hi)
        print(f"    moved {lo:g} to {hi:g}: {int(pick.sum())}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
