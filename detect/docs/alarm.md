# alarm

`alarmed_rows(scores, threshold, rule_hit, segment, n, k)` is True on the rows that
raise an alarm.

A row is flagged when `rule_hit` is True on it or its score is above `threshold`. A row
the model did not score has a NaN score, so only a rule flags it.

An alarm is raised on a row when `k` of the last `n` rows are flagged.
`k_of_last_n(flag, segment, n, k)` does the count. It does not carry across a change of
`segment`, since the rows either side of one can be hours apart. Near the start of a
segment it counts the rows the segment has so far.

## Why not consecutive flags

A count of consecutive flagged rows starts again at every unflagged row. One unflagged
row in the middle of an attack resets it. An attack with one unflagged row in every ten
never reaches ten consecutive flagged rows. k of the last n keeps the flags before that
row.
