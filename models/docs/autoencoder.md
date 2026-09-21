# autoencoder

An autoencoder is trained on normal rows to compress each row into `latent_dim`
numbers and reconstruct it from them. It learns to reconstruct rows like the ones it
was trained on, so a row unlike them comes back with a large error. That error is the
row's score. An anomaly left in the training rows is learned as well, and its score
comes out low.

```python
torch.manual_seed(seed)
linear = LinearAutoencoder(signals=signals, latent_dim=k)
linear_losses = fit(train_rows, linear, epochs=epochs, batch=batch, rate=rate,
                    threshold=threshold, patience=patience)
linear_scores = residuals(test_rows, linear)

torch.manual_seed(seed)
nonlinear = NonlinearAutoencoder(signals=signals, latent_dim=k, hidden=hidden)
nonlinear_losses = fit(train_rows, nonlinear, epochs=epochs, batch=batch, rate=rate,
                       threshold=threshold, patience=patience)
nonlinear_scores = residuals(test_rows, nonlinear)
```

Each row of `train_rows` and `test_rows` is one moment on the bus, one column per
signal. The score averages the squared error over the columns, so a column with a
larger spread outweighs the rest unless every column is on the same scale.
[scoring](../../scoring) z-scores the rows before they get here, and passes every
value. The module sets none of its own.

| argument | what it decides |
|---|---|
| `signals` | how many columns a row has |
| `latent_dim` | how many numbers a row is compressed into. Fewer leave more of a normal row out of the reconstruction. At `signals` or more nothing has to be left out, so every row reconstructs and every score is near 0. |
| `hidden` | how many units the hidden layer of `NonlinearAutoencoder` has. Below `latent_dim` the hidden layer is the narrowest point, so a larger `latent_dim` changes nothing. Neither case raises an error. |
| `epochs` | the most times training may go through every training row |
| `batch` | how many rows are used for each update of the weights |
| `rate` | how far each update moves the weights, the learning rate of the Adam optimizer |
| `threshold` | the share an epoch has to cut from the best loss so far to count as an improvement |
| `patience` | how many epochs in a row may fail to improve before training stops |

`threshold` and `patience` make the same test as PyTorch's `ReduceLROnPlateau` with
`threshold_mode='rel'`. An epoch improves when its loss is below the best loss so far
times `1 - threshold`, and only then does the best loss move. The share is relative
because the loss spans orders of magnitude across `latent_dim`, so no one absolute
amount fits every run.

`fit` trains the autoencoder in place and returns its mean loss on the training rows
for each epoch it ran. The losses only say whether training converged. They are
measured on the rows it trained on, so they say nothing about rows it has not seen.
Fewer losses than `epochs` means training stopped because the loss stopped improving.
A stop on the last epoch also leaves as many losses as `epochs`, so it cannot be told
apart from running to the limit. A loss that is NaN or infinite raises
`FloatingPointError`, since it would never trip the stop and training would run on.

`torch.manual_seed` seeds both the starting weights and the order `fit` shuffles the
rows in, since building the autoencoder draws from the same random numbers first. So
each autoencoder gets its seed right before it is built, and is trained before the
next is built. Running the same code again then gives the same autoencoders.

`residuals` gives each row one score, the mean of the squared differences between the
row and its reconstruction. The higher the score, the less the row looks like the
training rows.

| class | layers | what it can reconstruct |
|---|---|---|
| `LinearAutoencoder` | one linear layer to `latent_dim` and one back | rows on a flat surface through the training rows |
| `NonlinearAutoencoder` | a hidden layer of `hidden` units with ReLU on each side of `latent_dim` | rows on a surface of flat pieces joined at bends |

[calibrate](calibrate.md) sets the score above which a row is flagged.
