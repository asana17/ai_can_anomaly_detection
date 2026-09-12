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

`seconds_above`, `scaled_rows` and `attack_set` each read every log, so their results
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

## The split and calibration parameters

| name | value | what it is |
|---|---|---|
| `TRAIN` | 0.75 | the share of the seconds above 5 km/h before the test cut |
| `TARGET` | 0.001 | the share of the calibration rows the threshold cuts off |
| `CALIBRATION` | 0.10 | the share of the training seconds above 5 km/h that become the calibration set |
| `BLOCK` | 20 s | the seconds above 5 km/h in one calibration window |
| `GAP` | 5 s | the time either side of a calibration window where training rows are dropped |

None of these was chosen by looking at the test set.

- **`TRAIN`** is where the test period starts.
- **`TARGET`** is the false positive rate the threshold aims at. Raising it lowers the
  threshold, which catches more attacks and more normal rows with them. A stated
  choice, not a calculation.
- **`CALIBRATION`** has to leave enough calibration rows to put a 1 - `TARGET`
  quantile on. 1 / `TARGET` rows is only the floor where the quantile starts to exist,
  and at the floor one single row holds it up. Raising it takes rows off the fit.
- **`BLOCK`** sets how many separate situations `CALIBRATION` buys. The truck's
  situation changes over about 20 seconds, so a window that long holds about one of
  them.
- **`GAP`** only has to cover the event it keeps out of both parts, which is seconds
  for a hard brake. Every one of them costs training rows, so it stays well under
  `BLOCK`.

## Tests

Run from the repository root.

```
python3 -m pytest
```
