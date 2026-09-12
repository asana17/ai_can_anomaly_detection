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

The threshold is a percentile of the model's residual over the calibration rows. The
calibration logs are held out of the training set, so every model is measured on rows
the model never saw. See [split](../assemble/docs/split.md).

The calibration logs have to be separate from the training logs. A model with enough
capacity fits its own training rows. Residuals computed on the same rows the model
was fitted on come out smaller than on rows it has not seen. A threshold taken from
the training rows would then be too low, and more normal rows would sit above the
threshold than asked for.

## The calibration parameters

| name | value | what it is |
|---|---|---|
| `TARGET` | 0.1% | the share of the calibration rows that sit above the threshold |
| `CALIBRATION` |  | the share of the training logs with rows above 5 km/h that becomes the calibration set |

None of these values was chosen by looking at the test set.

- **`TARGET`** Raising the value lowers the threshold. More rows then sit above the
  threshold, which catches more attacks and more normal rows with them. Every
  calibration row is normal, so the share is a false positive rate. No calculation
  produces the value.
- **`CALIBRATION`** Raising the value moves logs from the training set into the
  calibration set. More calibration logs bring the false positive rate closer to
  `TARGET`. Fewer training logs give the model less to fit on. The value is the
  smallest one that still reaches `TARGET`.

## Tests

Run from the repository root.

```
python3 -m pytest
```
