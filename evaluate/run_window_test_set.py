"""Count what each window model adds to the alarm on every tick, on the attacked test
rows."""

from __future__ import annotations

import numpy as np

from detect.alarm import windows_above, windows_with_k_flagged
from evaluate.count_alarms import count_false_positive_window_alarms
from evaluate.run_test_set_common import attacks_caught_by_alarms
from preprocess.features.windows import window_ends


def caught_by_windows(alarmed, ends, position, stride, rows, attacks):
    """What alarmed windows caught, and their false positive alarms per hour.

    A window alarms at its last row, so it catches an attack when that row is in it.
    """
    at_last_rows = np.zeros(len(position), bool)
    at_last_rows[ends[alarmed]] = True
    alarms = count_false_positive_window_alarms(alarmed, ends, position, stride,
                                                attacks.injected)
    return {**attacks_caught_by_alarms(at_last_rows, attacks),
            "alarms_per_hour": float(alarms / rows.hours)}


def detection_with_one_window_model(flag, window_scores, threshold, rows_in_window,
                                    position, rows, attacks, strides):
    """At each of `strides` and each k, what the rows' flags caught on the windows of
    `rows_in_window` rows, and what they caught with the window model added.

    The rows' flags alarm a window when k of its rows are flagged.
    """
    kept = []
    for stride in strides:
        ends = window_ends(position, rows=rows_in_window, stride=stride)
        above = windows_above(window_scores, threshold, ends)
        for k in range(1, rows_in_window + 1):
            alone = windows_with_k_flagged(flag, ends, rows_in_window, k)
            kept.append({
                "stride": stride, "k": k,
                "every_tick": caught_by_windows(alone, ends, position, stride, rows,
                                                attacks),
                "with_window_model": caught_by_windows(alone | above, ends, position,
                                                       stride, rows, attacks)})
    return kept
