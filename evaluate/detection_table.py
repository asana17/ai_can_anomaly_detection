"""Put what test runs and window test runs caught side by side, as Markdown tables.

    python3 -m evaluate.detection_table runs_repo revision listed.json local_dir runs_dir out.md

`listed.json` names the directories of `runs_repo` to read, as
`{"test_runs": [...], "window_test_runs": [...]}`. Each is read at `revision`, and the
test set and log split it names at the commits it names them at.
"""

from __future__ import annotations

import json
import os

from common.cli import arguments
from common.hub_dirs import read_dir
from models.fits import model_from

KEPT = ("threshold", "false_positive_rate")     # what an entry adds to its model


def model_name(entry):
    """The name of the model a detection entry was counted with, its threshold and
    what it caught at each k left out."""
    return model_from({key: value for key, value in entry.items()
                       if key not in KEPT and not key.isdigit()}).name


def labels_of(test_run, local_dir):
    """The fold, attack and seed of the test run whose `meta.json` is `test_run`."""
    at = test_run["test_set"]
    _, test_set = read_dir(at["repo"], at["path"], local_dir, at["revision"],
                           repo_type="dataset")
    at = test_run["log_split"]
    _, log_split = read_dir(at["repo"], at["path"], local_dir, at["revision"],
                            repo_type="dataset")
    return (log_split["inputs"]["fold"], test_set["inputs"]["attack"],
            test_set["inputs"]["seed"])


def gain(window_at_k, instant):
    """What an alarm with a window model caught over the instant alarm alone at the k
    with no more false alarms that catches the most, or None when no k has as few."""
    fair = [at_k["found_worth_catching"] for key, at_k in instant.items()
            if key.isdigit()
            and at_k["alarms_per_hour"] <= window_at_k["alarms_per_hour"]]
    return window_at_k["found_worth_catching"] - max(fair) if fair else None


def rows_of(runs_repo, revision, listed, local_dir, runs_dir):
    """`{(fold, attack, seed): {detector: (its entry, the instant entry it is compared
    with or None)}}` and the worth catching attacks of each, from the directories
    `listed`. A detector counted twice for one fold, attack and seed raises, unless it
    is the rules and both counted the same, as two test runs of one test set do."""
    counted, worth, came_from = {}, {}, {}

    def test_run_at(path, at_revision):
        folder, meta = read_dir(runs_repo, path, runs_dir, at_revision)
        with open(os.path.join(folder, "detection.json")) as f:
            detection = json.load(f)
        key = labels_of(meta, local_dir)
        worth[key] = meta["attacks_worth_catching"]
        return key, detection

    def keep(key, name, kept, path):
        if name == "rules" and counted.get(key, {}).get(name) == kept:
            return
        if name in counted.setdefault(key, {}):
            raise ValueError(f"{name} on fold {key[0]}, {key[1]}, seed {key[2]} comes "
                             f"from both {came_from[key, name]} and {path}")
        counted[key][name], came_from[key, name] = kept, path

    for path in listed["test_runs"]:
        key, (rules, *instants) = test_run_at(path, revision)
        keep(key, "rules", (rules, None), path)
        for entry in instants:
            keep(key, f"rules + {model_name(entry)}", (entry, None), path)
    for path in listed["window_test_runs"]:
        folder, meta = read_dir(runs_repo, path, runs_dir, revision)
        at = meta["test_run"]
        key, detection = test_run_at(at["path"], at["revision"])
        instants = {model_name(entry): entry for entry in detection[1:]}
        with open(os.path.join(folder, "window_detection.json")) as f:
            for entry in json.load(f):
                instant = model_name(entry["instant"])
                keep(key, f"rules + {instant} + {model_name(entry['window'])}",
                     (entry, instants[instant]), path)
    return counted, worth


def cell(caught, worth, per_hour, more=None):
    text = f"{caught}/{worth}, {per_hour:.1f}/h"
    return text if more is None else f"{text}, {more:+d}"


def table(rows, ks):
    """A Markdown table of `rows`, `{detector: [cell at each of ks]}`."""
    return ["| detector | " + " | ".join(f"k={k}" for k in ks) + " |",
            "|---|" + "---|" * len(ks),
            *(f"| {name} | " + " | ".join(cells) + " |"
              for name, cells in rows.items()),
            ""]


def together(counted, worth, keys, name, k):
    """One detector at `k` over the runs of `keys` that hold it: caught and worth
    summed, false alarms an hour averaged, and a window model's gain summed."""
    held = [key for key in keys if name in counted[key]]
    caught = sum(counted[key][name][0][k]["found_worth_catching"] for key in held)
    per_hour = sum(counted[key][name][0][k]["alarms_per_hour"]
                   for key in held) / len(held)
    gains = [gain(counted[key][name][0][k], counted[key][name][1])
             for key in held if counted[key][name][1] is not None]
    more = sum(gains) if gains and None not in gains else None
    return cell(caught, sum(worth[key] for key in held), per_hour, more)


def tables(counted, worth):
    """The Markdown of the tables of each attack with its runs together, then of each
    run."""
    keys = sorted(counted)
    ks = [k for k in next(iter(counted[keys[0]].values()))[0] if k.isdigit()]
    out = ["## Each attack, its runs together", "",
           "Caught of the attacks worth catching, false alarms an hour, and for a "
           "window model what it catches over the instant alarm alone at the k with "
           "no more false alarms that catches the most. Caught, worth and gain are "
           "summed over the runs that hold the detector, and false alarms averaged.",
           ""]
    for attack in sorted({key[1] for key in keys}):
        mine = [key for key in keys if key[1] == attack]
        names = dict.fromkeys(name for key in mine for name in counted[key])
        out += [f"### {attack}", "",
                "Runs: " + ", ".join(f"fold {f} seed {s}" for f, _, s in mine), ""]
        out += table({name: [together(counted, worth, mine, name, k) for k in ks]
                      for name in names}, ks)
    out += ["## Each run", ""]
    for key in keys:
        out += [f"### fold {key[0]}, {key[1]}, seed {key[2]}", ""]
        out += table({name: [together(counted, worth, [key], name, k) for k in ks]
                      for name in counted[key]}, ks)
    return "\n".join(out)


def main(runs_repo, revision, listed_path, local_dir, runs_dir, out_path):
    with open(listed_path) as f:
        listed = json.load(f)
    counted, worth = rows_of(runs_repo, revision, listed, local_dir, runs_dir)
    head = ["# Detection table", "", f"Read from `{runs_repo}` at `{revision}`.", "",
            "```json", json.dumps(listed, indent=2), "```", ""]
    with open(out_path, "w") as f:
        f.write("\n".join(head) + tables(counted, worth) + "\n")


if __name__ == "__main__":
    main(**arguments(("runs_repo", "revision", "listed_path", "local_dir", "runs_dir",
                      "out_path")))
