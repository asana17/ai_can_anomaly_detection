"""Build the test arrays with attacks in them, and say which rows they cover.

    python3 -m assemble.test_set repo revision log_splits/<time> data_dir local_dir [--rebuild]
"""

from __future__ import annotations

import json
import itertools
import os
import random

import numpy as np

from attack.inject import inject
from assemble.grid import read_grid, starts_segment, to_arrays
from assemble.injected_frames import write_and_pass_frames
from assemble.split_test_logs import read_log_split
from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import Settings
from preprocess.features.grid_sample import resample
from preprocess.features.moving import moving, moving_spans
from preprocess.features.signal_state import SIGNALS
from preprocess.frames.can_log_loader import load_can_log

ARRAYS = ("raw", "t", "seg", "label", "wheel")      # what attacked_log builds a row of


def inject_frames(logs, rng: random.Random, source_logs=(), *, rows_before_attack,
                  period: float, max_hold: float, min_speed: float):
    """Try one replay in each log, and yield its frames before and after it, and its rows.

    Each item is the path, the frames, the frames with the attack in, and the rows and
    attack `attacked_log` gives, or the same frames twice and None for the attack when
    no attack landed. `source_logs` are the logs the replayed payloads are taken from,
    each log itself when there are none, and `rows_before_attack(log)` gives a log's
    rows by time. The replay copies from moving rows onto moving rows, and lands only
    when every row it changed is still moving.
    """
    pool = [(list(load_can_log(p)),
             moving_spans(rows_before_attack(p), min_speed=min_speed, period=period))
            for p in source_logs]
    for path in logs:
        frames = list(load_can_log(path))
        before = rows_before_attack(path)
        spans = moving_spans(before, min_speed=min_speed, period=period)
        donor, source_spans = rng.choice(pool) if source_logs else (frames, spans)
        made = inject(frames, rng, source_log=donor, spans=spans,
                      source_spans=source_spans)
        if made:
            rows, attack = attacked_log(*made, before, period=period, max_hold=max_hold)
            changed = rows["label"]
            if (attack is not None and np.all(rows["wheel"][changed] > min_speed)
                    and moving(rows["raw"][changed], min_speed=min_speed).all()):
                yield path, frames, made[0], rows, attack
                continue
        rows, _ = attacked_log(frames, None, {}, period=period, max_hold=max_hold)
        yield path, frames, frames, rows, None


def attacked_log(hurt, span, before, *, period: float, max_hold: float):
    """One attacked log on the grid, and the attack in it, or None.

    `before` is the log's rows by time before the attack, empty when none landed.

    | key | holds |
    | `raw`, `t`, `seg` | the rows, their times, segment ids counting from 0 |
    | `label` | True where the attack changed the row |
    | `wheel` | the wheel speed before the attack |

    The attack is `span` with `first` and `last` added, in this log's rows.
    """
    ticks = list(resample(hurt, period, max_hold))
    times = np.asarray([t for t, _ in ticks], np.float64)
    rows = np.asarray([row for _, row in ticks], np.float32)
    seg = np.cumsum(np.concatenate([[0], np.diff(times) > period * 1.5]))

    known = np.array([t in before for t in times], bool)
    if span is not None and not known.any():
        raise ValueError("no row lines up with the rows before the attack, which are "
                         "on another grid")
    # a grid holds float32, so the rows it did not hold are cast to match the ones it did
    clean = np.asarray([before[t] if seen else row
                        for t, seen, row in zip(times, known, rows)], np.float32)
    # NaN is a value J1939 reserves, the same on both sides when the attack left it
    changed = (rows != clean) & ~(np.isnan(rows) & np.isnan(clean))
    label = known & changed.any(axis=1)

    one = {"raw": rows, "t": times, "seg": seg.astype(np.int32), "label": label,
           "wheel": clean[:, SIGNALS.index("wheel_speed")]}
    covered = np.flatnonzero(label)
    if span is None or not len(covered):
        return one, None
    return one, dict(span, first=int(covered[0]), last=int(covered[-1]))


def _starts(sizes):
    """Where each part begins once the parts are laid end to end."""
    return [0, *itertools.accumulate(sizes[:-1])]


def grid_rows_injected(injected):
    """Every log of `injected` on the grid, laid end to end.

    A log with no attack contributes its rows too. Each attack gets its `log`, and its
    `first` and `last` count over all the rows here.
    """
    parts, found = [], []
    for path, _, _, one, attack in injected:
        if not len(one["t"]):
            continue
        parts.append(one)
        found.append(None if attack is None else dict(attack, log=path))

    rows_at = _starts([len(one["t"]) for one in parts])
    segments_at = _starts([int(one["seg"][-1]) + 1 for one in parts])
    joined = {name: np.concatenate([one[name] for one in parts])
              for name in ("raw", "t", "label", "wheel")}
    joined["seg"] = np.concatenate([one["seg"] + at
                                    for one, at in zip(parts, segments_at)])
    attacks = [dict(attack, first=attack["first"] + at, last=attack["last"] + at)
               for attack, at in zip(found, rows_at) if attack is not None]
    return {"attacks": attacks, **joined}


def rows_before_each(grid_dir):
    """`log -> its rows by time`, read off a grid, built one log at a time."""
    raw, times, logs, counts = read_grid(grid_dir)
    ends = dict(zip(logs, np.cumsum(counts)))
    sizes = dict(zip(logs, counts))

    def of(log):
        end, count = ends[log], sizes[log]
        return dict(zip(times[end - count:end], raw[end - count:end]))

    return of


def donor_logs(non_test_logs, seconds, count):
    """The `count` non-test logs the replayed payloads are taken from, spread evenly over
    those with `seconds` above `MIN_SPEED`."""
    moving_logs = [log for log in non_test_logs if seconds[log] > 0]
    return moving_logs[::max(len(moving_logs) // count, 1)][:count]


def read_test_set(folder):
    """A test set's rows, and the attacks that were injected into them."""
    rows = {name: np.load(os.path.join(folder, f"attacked_{name}.npy"))
            for name in ARRAYS}
    with open(os.path.join(folder, "injected.json")) as f:
        return rows, json.load(f)


def fetch_test_set(repo, revision, test_path, local_dir):
    """The rows a test set holds, its attacks, and the directories they came from.

    The test set is read at `revision` of `repo`, and the log split and grid it names
    at the commits it names them at. `before` gives a log's rows as they were before the
    attack, which is what `moved` is measured against.
    """
    folder, meta = read_dir(repo, test_path, local_dir, revision, repo_type="dataset")
    log_split, grid = meta["log_split"], meta["grid"]
    _, log_split_meta = read_dir(log_split["repo"], log_split["path"], local_dir,
                                 log_split["revision"], repo_type="dataset")
    grid_dir, grid_meta = read_dir(grid["repo"], grid["path"], local_dir,
                                   grid["revision"], repo_type="dataset")
    rows, attacks = read_test_set(folder)
    return {**rows, "attacks": attacks, "before": rows_before_each(grid_dir),
            "min_speed": log_split_meta["inputs"]["min_speed"],
            "period": grid_meta["inputs"]["period"],
            "dataset": {"test_set": {"repo": repo, "revision": revision,
                                     "path": test_path},
                        "log_split": log_split, "grid": grid}}


def write_test_set(folder, repo, revision, log_split_path, data_dir, local_dir,
                   settings):
    """Write the attacked frames and rows, and return the log split and grid for
    meta.json."""
    log_split_dir, log_split_meta = read_dir(repo, log_split_path, local_dir, revision,
                                             repo_type="dataset")
    grid = log_split_meta["grid"]
    grid_dir, grid_meta = read_dir(grid["repo"], grid["path"], local_dir,
                                   grid["revision"], repo_type="dataset")
    period, max_hold = (grid_meta["inputs"][n] for n in ("period", "max_hold"))
    cut = read_log_split(log_split_dir)
    with open(os.path.join(log_split_dir, "seconds.json")) as f:
        seconds = json.load(f)

    under = {name: [os.path.join(data_dir, p) for p in cut[name]]
             for name in ("non_test", "test")}
    before = rows_before_each(grid_dir)
    donors = donor_logs(cut["non_test"], seconds, settings.DONORS)
    if not donors:
        raise ValueError("no non-test log moves, so there is none to replay from")
    injected = inject_frames(under["test"], random.Random(settings.SEED),
                             [os.path.join(data_dir, p) for p in donors],
                             rows_before_attack=lambda log: before(
                                 os.path.relpath(log, data_dir)),
                             period=period, max_hold=max_hold,
                             min_speed=log_split_meta["inputs"]["min_speed"])
    got = grid_rows_injected(write_and_pass_frames(injected,
                                                   os.path.join(folder, "frames")))

    print(f"{len(got['t'])} rows from {len(cut['test'])} test logs, "
          f"{len(got['attacks'])} attacks", flush=True)
    for name in ARRAYS:
        np.save(os.path.join(folder, f"attacked_{name}.npy"), got[name])
    with open(os.path.join(folder, "injected.json"), "w") as f:
        json.dump([dict(a, log=os.path.relpath(a["log"], data_dir))
                   for a in got["attacks"]], f)
    return {"log_split": {"repo": repo, "revision": revision, "path": log_split_path},
            "grid": grid}


def main(repo, revision, log_split_path, data_dir, local_dir, rebuild=False):
    settings = Settings()
    inputs = {"log_split": log_split_path, "seed": settings.SEED,
              "donors": settings.DONORS}
    return reuse_or_make(repo, "test_sets", inputs, local_dir,
                         lambda folder: write_test_set(folder, repo, revision,
                                                       log_split_path, data_dir,
                                                       local_dir, settings),
                         rebuild, repo_type="dataset")


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "log_split_path", "data_dir", "local_dir"),
                    rebuild=False))
