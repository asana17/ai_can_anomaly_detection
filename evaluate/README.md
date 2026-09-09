# evaluate

Runs the whole comparison over a set of logs and prints what each layer catches.

```
python3 -m evaluate.run "data/part_*/*.csv" out
```

A third argument sets how many logs to sample. Without it the run takes 1,200,
spread evenly over the recording.

It splits the logs, builds the arrays, injects the attacks, scores the rules, then
sweeps PCA over its component counts. The numbers in [pca](../models/docs/pca.md)
come from this.

## What is reused

`driving_time`, `scaled_rows` and `attack_set` each read every log, so their results
are written to `out` and reused on the next run over the same logs.

`out/built.json` holds the logs and the settings they were built from. A run that
does not match it builds them again. Editing the code does not change that file, so
delete `out` after changing what these three do.

## An alarm is a run of rows, and `HOLD` says how long

Rules and models both flag single rows. A single flagged row is not an alarm here.
`HOLD` lists how many rows in a row a flag has to persist, and the report gives a
column for each, so one row and one second sit side by side.

Rows either side of a segment boundary can be hours apart. A run of flagged rows
therefore stops at a boundary, and `change_limit` only compares rows inside one
segment.

False alarms are counted as separate stretches per hour of clean driving, not as a
share of rows. Attacks last seconds, so counting rows for one and events for the
other compares different things.

## Only what the rules pass

Detection counts the attacks the rules missed, and the false alarm rate is taken over
the rows the rules let through. A model is credited for neither.

## The threshold comes from train

It is the 99.9th percentile of the residual over training rows that are moving and
that the rules pass.

Standard practice is a held-out set, because a model reconstructs its own training
rows too well and the threshold comes out low. PCA does not do that here. Its
residual p99.9 on train runs above the same figure on test, and a threshold from all
200,644 train rows landed 1.6 times off the rate asked for against 3.4 times from
14,659 held out rows.

A model with enough parameters to fit its training rows will need a held-out set, and
it has to be the same set for every model being compared.

## Tests

Run from the repository root.

```
python3 -m pytest
```
