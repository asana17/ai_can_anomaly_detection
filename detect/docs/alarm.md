# alarm

`alarmed_rows(scores, threshold, rule_hit, segment, hold)` is True on the rows that
raise an alarm.

A row is flagged when `rule_hit` is True on it or its score is above `threshold`. A row
the model did not score has a NaN score, so only a rule flags it.

An alarm is raised on the row that completes `hold` flagged rows in a row. A run does
not carry across a change of `segment`. `persistent(flag, segment, need)` counts the
run.
