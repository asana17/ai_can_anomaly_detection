# datasets

Turns a chronological file split into the arrays the autoencoder trains on. Each
row is one grid sample of the signals, and the z-score is fit on train alone, then
reused for validation and test so no future data leaks into the scaling.

```python
files = sorted(glob("data/part_*/*.csv"))     # every log, oldest first
train, val, test = split(files, 0.70, 0.05)
data = build(train, val, test, period=0.1)
save(data, "out")
```

`build` returns each split as an array of shape `(rows, signals)`, plus the `mean`
and `std` fit on train. `save` writes them, and the stats, as `.npy` files for the
model.
