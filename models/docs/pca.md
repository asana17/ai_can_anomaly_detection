# pca

The job is to notice traffic that is not normal. [rules](../../rules) cover what
someone could write down as an invariant. An attack that breaks none of them still
gets through. PCA is the model chosen for that gap.

```python
space = subspace(train_rows, components=12)  # keep 12 of the 17 directions as normal
score = residuals(test_rows, space)          # how far each row sits off them
variance_share(train_rows)                   # what each direction holds, to choose 12
```

The subspace passes through the mean of the rows it was fitted on, not through the
origin, so `Subspace` carries that mean and `residuals` subtracts it before
projecting.

## What it adds over a rule

A row is 17 numbers. The signals move together, so normal rows do not scatter through
the 17 dimensions. They gather in a long thin cloud.

PCA measures which way that cloud is stretched, and orders the 17 directions by how
far it reaches along each. Three of them hold 85% of the spread here. The thinnest
hold a thousandth. Along those, normal rows barely move at all.

The widest few span a subspace. The residual is how far a row lies outside it. A row
that moves along a thin direction has a large one, and normal traffic does not move
there.

A rule is a relationship someone identified and wrote as a formula. Two of the thin
directions are exactly that. The three speed signals carry one quantity, which
[speed_agreement](../../rules/instant/docs/speed_agreement.md) and
[shaft_ratio](../../rules/instant/docs/shaft_ratio.md) already check. The rest were
never written down, and PCA finds them in the data.

## What it cannot see

The residual is a distance to the subspace, not to the data. A row can sit far from
anything ever recorded and still have a residual of zero, as long as it lies along
the directions normal rows vary in. PCA is linear, so it cannot close that gap.

## How many directions to keep

There is no right number, so the comparison runs several and gives each a line.
[evaluate](../../evaluate) labels them `k`.

Keeping fewer leaves more of the normal variation in the residual, which raises the
threshold and hides small attacks. Keeping more fits the subspace tightly enough to
fit the attacks too.

## Its threshold comes from train

PCA does not reconstruct its training rows better than the test rows. Its residual
p99.9 on train runs above the same figure on test. A threshold from all 200,644 train
rows landed 1.6 times off the rate asked for, against 3.4 times from 14,659 held out
rows, which were too few to read a p99.9 off.

## What it scores on this data

Not measured on the current pipeline. The last figures were taken before the test set
was fixed, when most injected attacks moved the state less than ordinary traffic does
between two rows, so they said more about the test set than about PCA. Rerun
[evaluate](../../evaluate) and put the result here.

## A warning you can ignore

On numpy 2.0.2 against Apple Accelerate, plain matrix multiplication raises
`RuntimeWarning` for divide by zero, overflow and invalid value on ordinary finite
input. It comes from the backend rather than from anything here. The same three
appear in float64. Every residual stays finite. float32 and float64 agree to 2.8e-6
relative, measured over an attacked test set on 2026-09-09. `python3 -W ignore`
silences it.

The warning is left in place. Suppressing it with `np.errstate` would hide a real
numerical fault as well.
