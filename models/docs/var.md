# var

A window model. It scores a window of `rows` rows by how far its last row sits from
what the rows before it predict.

```python
fitted = autoregression(train_windows)   # windows of shape (windows, rows, signals)
score = residuals(test_windows, fitted)  # mean squared error on each last row
```

Each window is oldest first. The last row is predicted as a linear function of every
row before it in the window, with an intercept. `LinearRegression` of scikit-learn
solves it by least squares. `Autoregression` keeps its `coef_` and `intercept_`, so a
fit read back from `weights.safetensors` scores the same way.

## Why it is fitted

It is the baseline of the window models. It uses only how a row follows the rows
before it, in a linear way. A window autoencoder is measured against it, to tell what
the order of the rows gives alone from what the autoencoder adds.

## How many rows

`rows` is how many rows a window holds. Every row before the last is used, so `rows`
sets both the window and how far back the prediction reaches. There are
`(rows - 1) * signals` coefficients per signal. [fit_windows](fit_windows.md) fits
several values of `rows`. None was chosen by looking at an attack.
