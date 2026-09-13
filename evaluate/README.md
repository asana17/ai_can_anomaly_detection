# evaluate

Runs the whole comparison over a set of logs. The report gives one line to each of
these.

- the instant rules, which read physical values
- PCA, which flags a row whose residual is over the threshold, one line for each
  component count

```
python3 -m evaluate.run "data/part_*/*.csv" out
```

Without a third argument the run takes every log the pattern matches. Giving one samples
that many, spread evenly over the recording, which is a smoke test and not a
measurement.

It splits the logs, builds the arrays, injects the attacks, then asks the rules and
each model for one flag per row. The runs of flags, the counting and the table are
the same for all of them.

## What is reused

`seconds_above`, `grid_rows` and `attack_set` each read every log, so their results
are written to `out` and reused on the next run over the same logs.

`out/grid.json` holds the training logs the grid was built from. The calibration
settings are not in it, so a run with another `CALIBRATION`, `BLOCK` or `GAP` reads
the saved grid.

`out/built.json` holds the logs and the settings the attack set was built from.
`CALIBRATION`, `BLOCK` and `GAP` are among them. They decide which rows are left to
train, and the mean and std of those rows are what the attack set is z-scored on. The
std is also the unit each attack's `moved` is measured in, which decides whether the
attack is scored.

Editing the code changes neither file, so delete `out` after changing what these three
do.

## What counts as an alarm

A flag has to persist over several rows in a row to count as an alarm. `HOLD` sets
how many, and the report has a column for each value in it.

A run of flagged rows ends at a segment boundary, since rows either side of one can
be hours apart.

Only rows above 5 km/h are scored, and an attack counts only if it reaches one and
moved it by at least one standard deviation.

Detection is the number of those attacks with an alarm inside them. False alarms are
the number of alarms raised outside any attack, per hour of the rows above 5 km/h.

The floor is `rules/instant` alone. A rate rule needs the reading before, which a
model reading one instant is not given. The rate rules join the floor for the windowed
models.

## The split and calibration parameters

| name | value | what it is |
|---|---|---|
| `MIN_SPEED` | 5.0 km/h | the speed a row has to exceed to be scored |
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
  A stated choice, not a calculation. The report prints the share of clean test rows
  each threshold cuts, which is the check that it reaches `TARGET`.
- **`BLOCK`** sets how many separate situations `CALIBRATION` buys. The truck's
  situation changes over about 20 seconds, so a window that long holds about one of
  them. A stated choice, not a calculation.
- **`GAP`** only has to cover the event it keeps out of both parts, which is seconds
  for a hard brake. Every one of them costs training rows, so it stays well under
  `BLOCK`.

## Tests

Run from the repository root.

```
python3 -m pytest
```
