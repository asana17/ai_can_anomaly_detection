# pc run

## What is reused

`seconds_above`, `grid_rows` and `attack_set` each read every log, so their results
are written to `out` and reused on the next run over the same logs.

`out/grid.json` holds the training logs the grid was built from. The calibration
settings are not in it, so a run with another `CALIBRATION`, `BLOCK` or `GAP` reads
the saved grid.

`out/built.json` holds the logs and the settings the attack set was built from. It
includes `CALIBRATION`, `BLOCK` and `GAP`, because the attack set is z-scored with the
mean and std of the training rows they leave.

Editing the code changes neither file, so delete `out` after changing what these three
do.

## What counts as an alarm

A flag has to persist over several rows in a row to count as an alarm. `HOLD` lists
how many, and every value in it is counted.

A run of flagged rows ends at a segment boundary, since rows either side of one can
be hours apart.

Only rows above 5 km/h are scored. An attack is counted when it reaches one of them
and its largest change to a row, as the norm over the z-scored signals, is at least
`MOVED`. `MOVED` 1.0 is a judgement that drops replays whose copied values nearly
match the ones they overwrite.

Whether a row is above 5 km/h is decided by its speed before the attack. An attack
that fakes a stop stays in the count. The detectors read the attacked speed, so a detector that ignores
the row misses it.

Detection is the number of those attacks with an alarm inside them. False alarms are
the number of alarms raised outside any attack, per hour of the rows above 5 km/h.

With a model added, a row is flagged when a rule flags it or the model's score is over
its threshold. PCA's score is the residual, the autoencoder's the reconstruction error.
Each threshold comes from the calibration rows at `TARGET`.

Neither model reads a window, so both are compared with `rules/instant` only.

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
  A stated choice, not a calculation.
- **`BLOCK`** sets how many separate situations `CALIBRATION` buys. The truck's
  situation changes over about 20 seconds, so a window that long holds about one of
  them. A stated choice, not a calculation.
- **`GAP`** only has to cover the event it keeps out of both parts, which is seconds
  for a hard brake. Every one of them costs training rows, so it stays well under
  `BLOCK`.

## The autoencoder parameters

| name | value | how it was set |
|---|---|---|
| `EPOCHS` | 500 | a cap. The report shows how many epochs each fit ran, and fewer than 500 means it stopped on its own. |
| `BATCH` | 1024 | from 1024 and 4096, on how close the linear autoencoder's training loss came to PCA's and how long it took. No attack was used. The nonlinear autoencoder uses the same value. |
| `RATE` | 1e-3 | Adam's default in PyTorch |
| `IMPROVEMENT` | 1e-4 | the default `threshold` of PyTorch's `ReduceLROnPlateau` |
| `PATIENCE` | 10 | the default `patience` of the same |
| `TORCH_SEED` | 0 | a stated choice |
| `HIDDEN` | 32, 64, 128 | a stated choice. All of them are at least `signals`, so `latent_dim` stays the narrowest layer at every `k`. Each is reported. |

`BATCH` was compared at every `k`. Up to `k` 14 the two sizes came within 0.3% of each
other and within 0.8% of PCA, and 1024 took less time at every `k`. At `k` 16 1024
came within 13% and 4096 within 98%.
