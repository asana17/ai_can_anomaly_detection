"""The rows a detector reads, and how the flags it raises are counted."""

from __future__ import annotations

import numpy as np

from assemble.grid import moving
from rules.hits import rule_hits


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


def moved_by(attack, attacked, std):
    """How far `attack` took a row from the one the bus really produced.

    It is the largest distance over the rows the attack changed, between the attacked
    row and the original, divided by `std`. That is the train set's, so the distance
    is in the units a model reads. `attacked` holds the attacked rows and `before`,
    which gives a log's rows as they were.
    """
    original = attacked["before"](attack["log"])
    changed = [i for i in range(attack["first"], attack["last"] + 1)
               if attacked["label"][i]]
    return float(max(np.linalg.norm((attacked["raw"][i] - original[attacked["t"][i]])
                                    / std) for i in changed))


def prepare_scoring_input(got, scale, settings):
    """Work out what a detector reads and what it is judged against.

    The rows come back first, then the attacks. `rows_to_score` holds the rows a
    detector reads (`rows`), which of them are above `MIN_SPEED` (`mv`), which carry
    no attack (`quiet`), where a rule fires (`rules`), the segment ids (`seg`), and how
    many hours the quiet rows cover.

    `attacks_to_check` holds every attack that was injected (`injected`), and which of
    them are scorable (`scorable`). An attack is scorable when it reaches a row whose
    speed before the attack was above `MIN_SPEED`, and moved a row by at least `MOVED`.
    The rest are left out of the rate, since no detector could be asked to catch them.
    """
    mv = moving(scale.undo(got["rows"]), min_speed=settings.MIN_SPEED)
    truth = got["wheel"] > settings.MIN_SPEED   # the speed before the attack
    quiet = truth & ~got["label"]
    moved = np.array([a["moved"] for a in got["attacks"]])
    rows_to_score = {"rows": got["rows"], "seg": got["seg"], "mv": mv, "quiet": quiet,
                     "rules": rule_hits(got["raw"], settings) & mv,
                     "hours": float(quiet.sum() * period_of(got["t"]) / 3600)}
    attacks_to_check = {"injected": got["attacks"],
                        "scorable": (touched(truth, got["attacks"])
                                     & (moved >= settings.MOVED))}
    return rows_to_score, attacks_to_check

