# evaluate

Runs the whole comparison over a set of logs. The report gives one line to each of
these.

- the rules, which read physical values
- PCA, which flags a row whose residual is over the threshold, one line for each
  component count

```
python3 -m evaluate.run "data/part_*/*.csv" out
```

A third argument sets how many logs to sample. Without it the run takes 1,200,
spread evenly over the recording.

It splits the logs, builds the arrays, injects the attacks, then asks the rules and
each model for one flag per row. The runs of flags, the counting and the table are
the same for all of them.

## What is reused

`driving_time`, `scaled_rows` and `attack_set` each read every log, so their results
are written to `out` and reused on the next run over the same logs.

`out/built.json` holds the logs and the settings they were built from. A run that
does not match it builds them again. Editing the code does not change that file, so
delete `out` after changing what these three do.

## What counts as an alarm

A flag has to persist over several rows in a row to count as an alarm. `HOLD` sets
how many, and the report has a column for each value in it.

A run of flagged rows ends at a segment boundary, since rows either side of one can
be hours apart.

Only rows above 5 km/h are scored, and an attack counts only if it reaches one and
moved it by at least one standard deviation.

Detection is the number of those attacks with an alarm inside them. False alarms are
the number of alarms raised outside any attack, per hour of the rows above 5 km/h.

## The threshold

It is the 99.9th percentile of the model's residual, over rows above 5 km/h that the
rules pass.

Those rows are training rows today. They have to come from a calibration set, a
stretch of the training period kept out of the fit, and it has to be the same set for
every model.

## Tests

Run from the repository root.

```
python3 -m pytest
```
