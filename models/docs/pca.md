# pca

Scores a row by how far it sits off the subspace normal traffic occupies.

```python
space = subspace(train_rows, components=12)  # keep 12 of the 17 directions as normal
score = residuals(test_rows, space)          # how much of a row falls outside them
variance_share(train_rows)                   # what each direction holds, to choose 12
```

Fit on normal rows, the components span the directions those rows vary in about their
mean. The subspace passes through that mean, not through the origin, so `Subspace`
carries it and `residuals` subtracts it before projecting.

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

On numpy 2.0.2 against Apple Accelerate, plain matrix multiplication raises
`RuntimeWarning` for divide by zero, overflow and invalid value on ordinary finite
input. It comes from the backend rather than from anything here. The same three
appear in float64. Every residual stays finite. float32 and float64 agree to 2.8e-6
relative, measured over an attacked test set on 2026-09-09. `python3 -W ignore`
silences it.

The warning is left in place. Suppressing it with `np.errstate` would hide a real
numerical fault as well.

## What it scores on this data

Not measured on the current pipeline. The last figures were taken before the test set
was fixed, when most injected attacks moved the state less than ordinary traffic does
between two rows, so they said more about the test set than about PCA. Rerun
[evaluate](../../evaluate) and put the result here.
