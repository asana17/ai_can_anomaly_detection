# moving

`moving(raw, min_speed)` is True where a row's `wheel_speed` is above `min_speed`.

`raw` is read in physical units, before any scaling. `min_speed` is in km/h like
`wheel_speed`.

## Why only the moving rows

The stages after `preprocess` use only the rows `moving` marks, for two reasons. An
anomaly on a truck that stands still does no harm worth detecting. A threshold taken on
the moving rows also does not carry to the stopped ones.

PCA was fitted on the moving train rows of `train_sets/20260921-234334`. Its threshold
was taken at `TARGET` 0.001 on the moving calibration rows. The table gives the share
of stopped rows over it. They are the rows of the train logs no stage used, less the
ones a rule hits.

| k | stopped, engine on | stopped, engine off |
|---|---|---|
| 2 | 0.078 | 0.033 |
| 4 | 0.074 | 0.043 |
| 8 | 0.415 | 0.044 |
