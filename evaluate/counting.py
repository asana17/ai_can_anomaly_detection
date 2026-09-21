"""The rows a detector reads, and how the flags it raises are counted.

`evaluate.pc.run` and `evaluate.pc.score` both score rows this way, so a number from
one is a number from the other.
"""

from __future__ import annotations

from functools import partial

import numpy as np

from assemble.grid import moving
from preprocess.features.signal_state import SIGNALS
from rules.instant import (engine_off, gear_ratio, pedal_conflict, range_check,
                           reverse_speed, shaft_ratio, speed_agreement, steering_sign,
                           stopped_shaft)


def instant(settings):
    """The instant rules, with the speed the moving ones start at."""
    return (range_check.violations, speed_agreement.violations,
            partial(shaft_ratio.violations, min_speed=settings.MIN_SPEED),
            partial(gear_ratio.violations, min_speed=settings.MIN_SPEED),
            partial(steering_sign.violations, min_speed=settings.MIN_SPEED),
            engine_off.violations, pedal_conflict.violations,
            stopped_shaft.violations, reverse_speed.violations)


def rule_hits(raw, settings):
    """True where an instant rule fires, read off physical values rather than scaled ones."""
    checks = instant(settings)
    return np.array([any(check(dict(zip(SIGNALS, row))) for check in checks)
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


def training_rows(data, scale, settings):
    """The moving training rows, and the calibration rows with no instant rule on them."""
    def above(rows):
        return moving(scale.undo(rows), min_speed=settings.MIN_SPEED)

    clean = ~rule_hits(data["calibration_raw"], settings)
    return (data["rows"][above(data["rows"])],
            data["calibration_rows"][above(data["calibration_rows"]) & clean])


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


def detection(flag, rows_to_score, attacks_to_check, settings):
    """How many attacks a flag finds at each `HOLD`, and how many alarms it raises."""
    out = []
    for need in settings.HOLD:
        on = persistent(rows_to_score["rules"] | flag, rows_to_score["seg"], need)
        out.append({"hold": need,
                    "found": found(on, attacks_to_check["injected"],
                                   attacks_to_check["scorable"]),
                    "alarms_per_hour": (alarms(on & rows_to_score["quiet"])
                                        / rows_to_score["hours"])})
    return out
