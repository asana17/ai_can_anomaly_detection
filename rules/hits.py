"""Which rows an instant rule fires on."""

from __future__ import annotations

from functools import partial

import numpy as np

from rules.instant import (engine_off, gear_ratio, pedal_conflict, range_check,
                           reserved_moving, reverse_speed, shaft_ratio, speed_agreement,
                           steering_sign, stopped_shaft)


def instant(settings):
    """The instant rules, with the speed the moving ones start at."""
    return (range_check.hits, speed_agreement.hits,
            partial(shaft_ratio.hits, min_speed=settings.MIN_SPEED),
            partial(gear_ratio.hits, min_speed=settings.MIN_SPEED),
            partial(steering_sign.hits, min_speed=settings.MIN_SPEED),
            engine_off.hits, pedal_conflict.hits, stopped_shaft.hits, reverse_speed.hits,
            reserved_moving.hits)


def rule_hits(raw, settings):
    """True where an instant rule fires, read off physical values rather than scaled ones."""
    hit = np.zeros(len(raw), bool)
    for check in instant(settings):
        hit |= check(raw)
    return hit
