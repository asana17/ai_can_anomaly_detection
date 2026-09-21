"""Which rows an instant rule fires on."""

from __future__ import annotations

from functools import partial

import numpy as np

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
