"""Which rows an instant rule fires on."""

from __future__ import annotations

from functools import partial

import numpy as np

from preprocess.features.moving import moving
from preprocess.features.windows import positions
from rules.instant import (engine_off, gear_ratio, pedal_conflict, range_check,
                           reserved_moving, reverse_speed, shaft_ratio, speed_agreement,
                           steering_sign, stopped_shaft)
from rules.sequence import (change_limit, frozen_signal, repeated_signal,
                            torque_over_load)


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


def hits_of_every_rule(raw, segments, min_speed):
    """True on the moving rows any rule fires on, instant or reading the rows before in
    the same unbroken span of moving rows."""
    mv = moving(raw, min_speed=min_speed)
    position = positions(mv, segments)
    return (rule_hits(raw, min_speed) | change_limit.hits(raw, position)
            | torque_over_load.hits(raw, position)
            | frozen_signal.hits(raw, position)
            | repeated_signal.hits(raw, position)) & mv
