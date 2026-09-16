"""The rows a detector reads, and how the flags it raises are counted.

`evaluate.pc.run` and `evaluate.board.compare` both score rows this way, so a number
from one is a number from the other.
"""

from __future__ import annotations

from functools import partial

import numpy as np

from assemble.split import moving
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
        return moving(scale.undo(rows), settings.MIN_SPEED)

    clean = ~rule_hits(data["calibration_raw"], settings)
    return (data["rows"][above(data["rows"])],
            data["calibration_rows"][above(data["calibration_rows"]) & clean])


def scored_set(got, scale, settings):
    """The attacked rows, what a detector reads in them, and what an alarm is counted in."""
    mv = moving(scale.undo(got["rows"]), settings.MIN_SPEED)
    truth = got["wheel"] > settings.MIN_SPEED   # what is scored, the speed before it
    quiet = truth & ~got["label"]
    moved = np.array([a["moved"] for a in got["attacks"]])
    return {"rows": got["rows"], "seg": got["seg"],
            "mv": mv,                           # what a detector reads, attack included
            "truth": truth, "quiet": quiet, "attacks": got["attacks"],
            "rules": rule_hits(got["raw"], settings) & mv,
            "scored": touched(truth, got["attacks"]) & (moved >= settings.MOVED),
            "hours": float(quiet.sum() * period_of(got["t"]) / 3600)}


def detection(flag, test, settings):
    """How many attacks a flag finds at each `HOLD`, and how many alarms it raises."""
    out = []
    for need in settings.HOLD:
        on = persistent(test["rules"] | flag, test["seg"], need)
        out.append({"hold": need,
                    "found": found(on, test["attacks"], test["scored"]),
                    "alarms_per_hour": alarms(on & test["quiet"]) / test["hours"]})
    return out
