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
