"""Run the whole comparison over a set of logs and print what each layer catches.

    python3 -m evaluate.run "data/part_*/*.csv" out [logs]
"""

from __future__ import annotations

import glob
import json
import os
import random
import sys
import time

import numpy as np

from assemble.attack_set import attack_set
from assemble.train_set import Scale, save, scaled_rows
from assemble.split import MIN_SPEED, driving_time, split
from models.pca import residuals, subspace
from preprocess.features.grid_sample import DEFAULT_MAX_HOLD, DEFAULT_PERIOD
from preprocess.features.signal_state import SIGNALS
from rules.instant import (engine_off, gear_ratio, pedal_conflict, range_check,
                           reverse_speed, shaft_ratio, speed_agreement, steering_sign,
                           stopped_shaft)
from rules.rate import change_limit

FILES = 1200            # logs to sample by default, spread evenly over the recording
TRAIN = 0.75            # share of the driving time before the test cut
DONORS = 24             # training logs the replayed payloads are taken from
SEED = 0                # the rng the attacks are drawn with
GRID = {"period": DEFAULT_PERIOD, "max_hold": DEFAULT_MAX_HOLD}
COMPONENTS = (2, 4, 6, 8, 10, 12, 14, 16)
TARGET = 0.1            # the false alarm rate in percent the threshold asks for
BANDS = ((1.0, 2.0), (2.0, 4.0), (4.0, np.inf))
HOLD = (1, 10)          # rows a flag must persist before it counts as an alarm
INSTANT = (range_check, speed_agreement, shaft_ratio, gear_ratio, steering_sign,
           engine_off, pedal_conflict, stopped_shaft, reverse_speed)
WHEEL = SIGNALS.index("wheel_speed")


def weights_for(logs, out_dir):
    """The driving time of each log, measured once and kept."""
    path = os.path.join(out_dir, "driving.json")
    if os.path.exists(path):
        kept = json.load(open(path))
        if set(kept) == set(logs):
            return kept
    measured = driving_time(logs)
    json.dump(measured, open(path, "w"))
    return measured


ARRAYS = ("rows", "raw", "t", "seg")
ATTACKED = ("rows", "raw", "t", "seg", "label")


def _have(out_dir, names):
    """True once every one of `names` is on disk."""
    return all(os.path.exists(os.path.join(out_dir, n)) for n in names)


def built_from(train, test):
    """The logs and the settings the saved files were built from.

    A run that does not match this builds them again. Editing the code leaves it
    unchanged, so delete `out` after that.
    """
    return {"logs": [train, test], "train": TRAIN, "donors": DONORS,
            "seed": SEED, "signals": SIGNALS, **GRID}


def arrays_for(train, test, out_dir):
    """The arrays, built once and read back on a later run over the same logs."""
    kept = os.path.join(out_dir, "built.json")
    shape = built_from(train, test)
    files = [f"{n}.npy" for n in ARRAYS] + ["mean.npy", "std.npy"]
    if (os.path.exists(kept) and json.load(open(kept)) == shape
            and _have(out_dir, files)):
        data = {n: np.load(os.path.join(out_dir, f"{n}.npy")) for n in ARRAYS}
        data["scale"] = Scale(np.load(os.path.join(out_dir, "mean.npy")),
                              np.load(os.path.join(out_dir, "std.npy")))
        return data, True
    data = scaled_rows(train, **GRID)  # the test rows come from the attack set
    save(data, out_dir)
    json.dump(shape, open(kept, "w"))
    return data, False


def attacks_for(train, test, scale, out_dir, rebuilt):
    """The attack set, kept beside the arrays it was cut from."""
    files = [f"attacked_{n}.npy" for n in ATTACKED] + ["attacked.json"]
    if not rebuilt and _have(out_dir, files):
        got = {n: np.load(os.path.join(out_dir, f"attacked_{n}.npy"))
               for n in ATTACKED}
        got["attacks"] = json.load(open(os.path.join(out_dir, "attacked.json")))
        return got, True
    got = attack_set(test, scale, random.Random(SEED), **GRID,
                     source_logs=train[::max(len(train) // DONORS, 1)][:DONORS])
    for name in ATTACKED:
        np.save(os.path.join(out_dir, f"attacked_{name}.npy"), got[name])
    json.dump(got["attacks"], open(os.path.join(out_dir, "attacked.json"), "w"))
    return got, False


def rule_hits(raw, segment, times):
    """True where any rule fires, read off physical values rather than scaled ones."""
    out = np.zeros(len(raw), bool)
    previous = None
    for i in range(len(raw)):
        values = dict(zip(SIGNALS, raw[i].tolist()))
        out[i] = any(rule.violations(values) for rule in INSTANT)
        if not out[i] and previous is not None and segment[i] == segment[i - 1]:
            out[i] = bool(change_limit.violations(values, previous,
                                                  float(times[i] - times[i - 1])))
        previous = values
    return out


def found(flags, attacks, pick):
    """How many of the picked attacks have a flagged row."""
    return sum(flags[a["first"]:a["last"] + 1].any()
               for a, keep in zip(attacks, pick) if keep)


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


def main(pattern, out_dir, files=FILES):
    os.makedirs(out_dir, exist_ok=True)
    logs = sorted(glob.glob(pattern))
    logs = logs[::max(len(logs) // files, 1)][:files]
    weight = weights_for(logs, out_dir)

    train, test = split(logs, TRAIN, weight)
    print(f"{len(train)} train, {len(test)} test logs, driving "
          f"{sum(weight[p] for p in train):.0f}s and "
          f"{sum(weight[p] for p in test):.0f}s", flush=True)

    clock = time.time()
    data, kept = arrays_for(train, test, out_dir)
    scale = data["scale"]
    how = "reused" if kept else f"in {time.time() - clock:.0f}s"
    print(f"arrays {how}, train {data['rows'].shape}", flush=True)

    clock = time.time()
    got, kept = attacks_for(train, test, scale, out_dir, not kept)
    how = "reused" if kept else f"in {time.time() - clock:.0f}s"
    print(f"attack set {how}, {len(got['attacks'])} attacks", flush=True)

    def moving(rows):
        return scale.undo(rows)[:, WHEEL] > MIN_SPEED

    train_pass = ~rule_hits(data["raw"], data["seg"], data["t"])
    tr = data["rows"][moving(data["rows"])]
    calibrate = data["rows"][moving(data["rows"]) & train_pass]
    rows, label = got["rows"], got["label"]
    mv = moving(rows)
    quiet = mv & ~label
    attacks = got["attacks"]
    reach = np.array([mv[a["first"]:a["last"] + 1].any() for a in attacks])
    moved = np.array([a["moved"] for a in attacks])
    scored = reach & (moved >= BANDS[0][0])
    print(f"moving rows: train {len(tr)}, test {int(mv.sum())}. "
          f"{int(scored.sum())} attacks reach a moving row and moved it")

    rules = rule_hits(got["raw"], got["seg"], got["t"])
    hours = quiet.sum() * period_of(got["t"]) / 3600
    print(f"\n{hours:.1f} hours of clean driving to raise a false alarm in")

    layers = [("rules", rules & mv)]
    for k in COMPONENTS:
        space = subspace(tr, k)
        cut = np.percentile(residuals(calibrate, space), 100 - TARGET)
        layers.append((f"pca k={k}", (residuals(rows, space) > cut) & mv))

    print(f"\n{'layer':>9}   " + "  ".join(f"found in {n}".rjust(11) for n in HOLD)
          + "   " + "  ".join(f"alarms/h {n}".rjust(12) for n in HOLD))
    for name, flag in layers:
        cells = []
        for need in HOLD:
            on = persistent(flag, got["seg"], need)
            cells.append((found(on, attacks, scored), alarms(on & quiet) / hours))
        print(f"{name:>9}   "
              + "  ".join(f"{c:>7}/{int(scored.sum()):<3d}" for c, _ in cells)
              + "   " + "  ".join(f"{a:12.1f}" for _, a in cells))

    print(f"\nwhat each layer leaves the next, at {HOLD[-1]} rows held")
    caught = persistent(rules & mv, got["seg"], HOLD[-1])
    left = scored & ~np.array([caught[a["first"]:a["last"] + 1].any() for a in attacks])
    print(f"  rules leave {int(left.sum())} of {int(scored.sum())} attacks")
    for lo, hi in BANDS:
        pick = left & (moved >= lo) & (moved < hi)
        print(f"    moved {lo:g} to {hi:g}: {int(pick.sum())}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else FILES)
