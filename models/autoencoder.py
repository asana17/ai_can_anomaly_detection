"""Score a row by how badly an autoencoder trained on normal rows reconstructs it.

An autoencoder compresses a row into `latent_dim` numbers and reconstructs it. There
are `LinearAutoencoder` and `NonlinearAutoencoder`, and `DeltaAutoencoder` for the steps
between the rows of a window, `DriftAutoencoder` for how far each row of a window
sits from its first, and `Conv1dAutoencoder` for the steps with 1D convolutions. `fit`
trains any of them.
"""

from __future__ import annotations

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


class LinearAutoencoder(nn.Module):
    """One linear layer from the signals to `latent_dim` and one back."""

    def __init__(self, signals: int, latent_dim: int):
        super().__init__()
        self.encoder = nn.Linear(signals, latent_dim)
        self.decoder = nn.Linear(latent_dim, signals)

    def forward(self, x):
        return self.decoder(self.encoder(x))


class NonlinearAutoencoder(nn.Module):
    """A hidden layer of `hidden` units with ReLU on each side of `latent_dim`."""

    def __init__(self, signals: int, latent_dim: int, hidden: int):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(signals, hidden), nn.ReLU(),
                                     nn.Linear(hidden, latent_dim))
        self.decoder = nn.Sequential(nn.Linear(latent_dim, hidden), nn.ReLU(),
                                     nn.Linear(hidden, signals))

    def forward(self, x):
        return self.decoder(self.encoder(x))


class DeltaAutoencoder(nn.Module):
    """`NonlinearAutoencoder` on the steps between the rows of a window of `rows` rows,
    each signal's step divided by its `step_std`.

    It returns the window with the error of each step it reconstructs added, so that the
    output less the input is that error, the first row's being 0. `fit` and `residuals`
    then measure the steps as they measure rows.
    """

    def __init__(self, rows: int, signals: int, latent_dim: int, hidden: int):
        super().__init__()
        self.rows, self.signals = rows, signals
        self.register_buffer("step_std", torch.ones(signals))
        self.steps = NonlinearAutoencoder((rows - 1) * signals, latent_dim, hidden)

    def forward(self, x):
        window = x.reshape(-1, self.rows, self.signals)
        # the end is counted from the start, since ST Edge AI Core cannot take a slice
        # that ends at a negative index
        step = ((window[:, 1:] - window[:, :self.rows - 1]) / self.step_std).flatten(1)
        error = self.steps(step) - step
        return x + torch.cat([torch.zeros_like(x[:, :self.signals]), error], dim=1)


class DriftAutoencoder(nn.Module):
    """`NonlinearAutoencoder` on how far each row of a window of `rows` rows sits from
    its first row, each value divided by `drift_std` for its row and signal.

    It returns the window with the error of each value it reconstructs added, as
    `DeltaAutoencoder` does, the first row's being 0.
    """

    def __init__(self, rows: int, signals: int, latent_dim: int, hidden: int):
        super().__init__()
        self.rows, self.signals = rows, signals
        self.register_buffer("drift_std", torch.ones(rows - 1, signals))
        self.drifts = NonlinearAutoencoder((rows - 1) * signals, latent_dim, hidden)

    def forward(self, x):
        window = x.reshape(-1, self.rows, self.signals)
        drift = ((window[:, 1:] - window[:, :1]) / self.drift_std).flatten(1)
        error = self.drifts(drift) - drift
        return x + torch.cat([torch.zeros_like(x[:, :self.signals]), error], dim=1)


class Conv1dAutoencoder(nn.Module):
    """An autoencoder of 1D convolutions along time, on the steps between the rows of a
    window of `rows` rows, each signal's step divided by its `step_std` as in
    `DeltaAutoencoder`.

    Two convolutions of `KERNEL` rows and stride 2 take the `rows - 1` steps of signals
    to `hidden` and then `latent_dim` channels, each a quarter as long in time, and two
    transposed ones take them back. It returns the window with the error of each step
    it reconstructs added, as `DeltaAutoencoder` does.
    """

    KERNEL = 5

    def __init__(self, rows: int, signals: int, latent_dim: int, hidden: int):
        super().__init__()
        self.rows, self.signals = rows, signals
        self.register_buffer("step_std", torch.ones(signals))
        pad = self.KERNEL // 2
        self.encoder = nn.Sequential(
            nn.Conv1d(signals, hidden, self.KERNEL, stride=2, padding=pad), nn.ReLU(),
            nn.Conv1d(hidden, latent_dim, self.KERNEL, stride=2, padding=pad))
        self.decoder = nn.Sequential(
            nn.ReLU(),
            nn.ConvTranspose1d(latent_dim, hidden, self.KERNEL, stride=2, padding=pad,
                               output_padding=1), nn.ReLU(),
            nn.ConvTranspose1d(hidden, signals, self.KERNEL, stride=2, padding=pad,
                               output_padding=1))

    def forward(self, x):
        window = x.reshape(-1, self.rows, self.signals)
        # the end is counted from the start, since ST Edge AI Core cannot take a slice
        # that ends at a negative index
        step = (window[:, 1:] - window[:, :self.rows - 1]) / self.step_std
        # (windows, signals, rows - 1), time along the last axis as Conv1d reads it
        rebuilt = self.decoder(self.encoder(step.transpose(1, 2)))
        rebuilt = rebuilt[:, :, :self.rows - 1].transpose(1, 2)
        error = (rebuilt - step).flatten(1)
        return x + torch.cat([torch.zeros_like(x[:, :self.signals]), error], dim=1)


def fit(rows: np.ndarray, model: nn.Module, epochs: int, batch: int, rate: float,
        threshold: float, patience: int) -> list[float]:
    """Train `model` on `rows` with Adam, and return the mean loss of each epoch.

    Stops once more than `patience` epochs in a row fail to bring the loss below
    `best * (1 - threshold)`, the test PyTorch's ReduceLROnPlateau makes with
    threshold_mode 'rel', or after `epochs`.
    """
    data = torch.from_numpy(np.asarray(rows, dtype=np.float32))
    optimizer = torch.optim.Adam(model.parameters(), lr=rate)
    criterion = nn.MSELoss()
    loader = DataLoader(TensorDataset(data), batch_size=batch, shuffle=True)
    model.train()
    losses, best, bad_epochs = [], float("inf"), 0
    for _ in range(epochs):
        total = 0.0
        for (x,) in loader:
            optimizer.zero_grad()
            loss = criterion(model(x), x)
            loss.backward()
            optimizer.step()
            total += loss.item() * len(x)
        losses.append(total / len(data))
        # a NaN loss fails every comparison below, so without this it would never stop
        if not np.isfinite(losses[-1]):
            raise FloatingPointError(f"loss is {losses[-1]} after epoch {len(losses)}")
        if losses[-1] < best * (1 - threshold):
            best, bad_epochs = losses[-1], 0
        else:
            bad_epochs += 1
        if bad_epochs > patience:
            break
    return losses


def residuals(rows: np.ndarray, model: nn.Module, signals: int) -> np.ndarray:
    """Each input's mean squared reconstruction error over its last `signals` values.

    An input is one row of `signals` values, or a window of rows laid out oldest first,
    where the last `signals` values are its last row.
    """
    data = torch.from_numpy(np.asarray(rows, dtype=np.float32))
    model.eval()
    with torch.no_grad():
        return ((model(data) - data)[:, -signals:] ** 2).mean(dim=1).numpy()
