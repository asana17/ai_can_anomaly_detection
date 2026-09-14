import numpy as np
import pytest
import torch
from torch import nn

from models.autoencoder import LinearAutoencoder, NonlinearAutoencoder, fit, residuals


def _rows(seed=0, signals=17, n=3000):
    rng = np.random.default_rng(seed)
    return rng.normal(size=(n, signals)).astype(np.float32)


def _trained(rows, epochs=1, threshold=float("-inf"), patience=0):
    torch.manual_seed(0)
    model = NonlinearAutoencoder(signals=17, latent_dim=4, hidden=8)
    losses = fit(rows, model, epochs=epochs, batch=256, rate=1e-3,
                 threshold=threshold, patience=patience)
    return model, losses


def test_there_is_one_residual_per_row():
    rows = _rows()
    model, _ = _trained(rows)
    assert residuals(rows, model).shape == (3000,)


def test_without_a_stop_every_epoch_runs():
    _, losses = _trained(_rows(), epochs=3)
    assert len(losses) == 3


def test_it_stops_once_the_loss_stops_improving_by_threshold():
    # noise cannot be learned, so no epoch after the first halves the loss
    _, losses = _trained(_rows(), epochs=50, threshold=0.5, patience=2)
    assert len(losses) == 4


def test_a_loss_that_is_not_finite_stops_training():
    rows = _rows()
    rows[0, 0] = np.nan
    with pytest.raises(FloatingPointError):
        _trained(rows, epochs=5)


def test_the_same_seed_gives_the_same_model():
    rows = _rows()
    first, _ = _trained(rows)
    second, _ = _trained(rows)
    assert np.array_equal(residuals(rows, first), residuals(rows, second))


def test_the_linear_one_is_one_layer_each_way():
    model = LinearAutoencoder(signals=17, latent_dim=4)
    assert isinstance(model.encoder, nn.Linear) and model.encoder.out_features == 4
    assert isinstance(model.decoder, nn.Linear) and model.decoder.out_features == 17
