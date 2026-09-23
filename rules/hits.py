"""Which rows an instant rule fires on."""

from __future__ import annotations

from functools import partial

import numpy as np

from rules.instant import (engine_off, gear_ratio, pedal_conflict, range_check,
                           reserved_moving, reverse_speed, shaft_ratio, speed_agreement,
                           steering_sign, stopped_shaft)


def instant(min_speed):
    """The instant rules, the moving ones starting at `min_speed`."""
    return (range_check.hits, speed_agreement.hits,
            shaft_ratio.hits,
            partial(gear_ratio.hits, min_speed=min_speed),
            partial(steering_sign.hits, min_speed=min_speed),
            engine_off.hits, pedal_conflict.hits, stopped_shaft.hits, reverse_speed.hits,
            reserved_moving.hits)


def rule_hits(raw, min_speed):
    """True where an instant rule fires, read off physical values rather than scaled ones."""
    hit = np.zeros(len(raw), bool)
    for check in instant(min_speed):
        hit |= check(raw)
    return hit
