"""Count what each window model adds to the alarm on every tick, on the attacked test
rows."""

from __future__ import annotations

from detect.alarm import alarmed_rows
from evaluate.run_test_set_common import (attacks_caught_by_alarms,
                                          false_positive_alarms_per_hour,
                                          threshold_given_to)


def detection_of_one_window_model(scores, threshold, window_scores,
                                    window_threshold, rows, attacks, n):
    """What the rules and the instant model caught at each k of the last `n` rows, with
    the window model's alarm added.

    The window model alarms on the last row of each window whose score is above
    `window_threshold`, the row it is judged at. A row where no window ends has NaN,
    which is never above it.
    """
    window_alarm = window_scores > window_threshold
    kept = {}
    for k in range(1, n + 1):
        alarmed = alarmed_rows(scores, threshold, rows.rule_hit, rows.segment, n,
                               k) | window_alarm
        kept[str(k)] = {**attacks_caught_by_alarms(alarmed, attacks),
                        "alarms_per_hour": false_positive_alarms_per_hour(alarmed, rows,
                                                                          attacks)}
    return kept


def detection_of_each_window_model(thresholds, models, scores, window_thresholds,
                           window_models, window_scores, rows, attacks, n):
    """What each instant model caught with the rules and each window model, each at the
    threshold it was given."""
    kept = []
    for model, column in zip(models, scores.T):
        threshold = threshold_given_to(thresholds, model)
        for window_model, window_column in zip(window_models, window_scores.T):
            window_threshold = threshold_given_to(window_thresholds, window_model)
            kept.append({"instant": {**model, "threshold": threshold},
                         "window": {**window_model, "threshold": window_threshold},
                         **detection_of_one_window_model(
                             column, threshold, window_column, window_threshold, rows,
                             attacks, n)})
    return kept
