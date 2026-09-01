# normalize

Puts every signal on the same scale with a z-score, so the model is not dominated
by signals that happen to carry large numbers.

## Example

```python
stats = fit(train_vectors)   # mean and std per signal, from training data only
normalize(vector, stats)     # (value - mean) / std, per signal
```

`fit` measures each signal's mean and spread over the training vectors only, so the
validation and test sets cannot leak into it. `normalize` then shifts and scales
any vector with those numbers.

## Why z-score, not min-max

min-max clips anything beyond the training range to the edge. z-score keeps it as a
large number instead, so a value never seen in training is marked unusual, not
thrown away. Values outside the physical range are caught by the rule checks, not
here.
