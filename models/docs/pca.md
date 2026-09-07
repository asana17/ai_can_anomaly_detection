# pca

Scores a row by how far it sits off the subspace normal traffic occupies.

```python
fit(rows, components)        # -> (signals, k) basis
residuals(rows, basis)       # -> one distance per row
explained(rows)              # -> the share of variance each component holds
```

Fit on normal rows, the components span the directions those rows vary in. Project a
row onto them, subtract, and what is left is the residual. A row pushed off the
subspace has a large one.

## What it cannot see

The residual is a distance to a subspace, not to the data. A row can sit far from
anything ever recorded and still have a residual of zero, as long as it lies along
directions normal rows vary in. That is the gap a model with a nonlinear map is meant
to close, and measuring it is why this exists.

## Choosing k

There is no right number, so the comparison runs several. Fewer components leave more
of normal variation in the residual, which raises the threshold and buries small
attacks. More components fit the subspace tightly, until it starts holding the
attacks too.

## A warning you can ignore

On numpy 2.0.2 with this machine's BLAS, plain matrix multiplication raises
`RuntimeWarning: divide by zero encountered in matmul` on ordinary finite input. It
comes from the backend rather than from anything here, the results match `einsum`
exactly, and `python3 -W ignore` silences it.

## What it scores on this data

Fit on 240,514 moving train rows, thresholds taken at the 99.9th percentile of
23,463 moving validation rows, and run against a test set holding 139 attacks, 54 of
which reach a moving row.

| k | threshold | attacks found | false alarms |
|---|---|---|---|
| 2 | 6.583 | 0 of 54 | 0.003% |
| 6 | 4.163 | 0 of 54 | 0.014% |
| 8 | 2.285 | 2 of 54 | 0.056% |
| 12 | 1.362 | 6 of 54 | 0.056% |
| 16 | 0.021 | 10 of 54 | 0.098% |

False alarms land near the 0.1% the threshold asks for, so the threshold carries from
validation to test. Detection does not follow. The best of these finds under a fifth
of the attacks.

Read the last row carefully. With 16 of 17 components the subspace is nearly the
whole space, the residual is one direction wide and the threshold is 0.021. Detection
rises with k because the residual shrinks around it, not because the subspace has
learned anything. This is the baseline a model with a nonlinear map has to beat, and
it is a low one.
