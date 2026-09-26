# alarm

`alarmed_rows(scores, threshold, rule_hit, segment, n, k)` is True on the rows that
raise an alarm.

A row is flagged when `rule_hit` is True on it or its score is above `threshold`.
`flagged_rows(scores, threshold, rule_hit)` gives these flags. A row the model did not
score has a NaN score, so only a rule flags it.

An alarm is raised on a row when `k` of the last `n` rows are flagged.
`k_of_last_n(flag, segment, n, k)` does the count. It does not carry across a change of
`segment`, since the rows either side of one can be hours apart. Near the start of a
segment it counts the rows the segment has so far.

## Windows

A window is given by the index of its last row. It holds that row and the `rows - 1`
rows before it.

`windows_with_k_flagged(flag, ends, rows, k)` is True for each window where `k` of its
`rows` rows are flagged. It turns the row flags into flags on the same windows a window
model scores, so the two can be compared.

`windows_above(window_scores, threshold, ends)` is True for each window whose score is
above `threshold`.

## Why not consecutive flags

A count of consecutive flagged rows starts again at every unflagged row. One unflagged
row in the middle of an attack resets it. An attack with one unflagged row in every ten
never reaches ten consecutive flagged rows. k of the last n keeps the flags before that
row.
