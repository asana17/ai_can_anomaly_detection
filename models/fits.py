"""The models a run fits, each knowing how it is fitted, named and built back.

Training fits a model here and keeps its tensors. Anything that scores rows later
takes the same model's tensors back out. `as_dict` and `model_from` are how one model is
written down and read back, `models_from` how a list of them is asked for.
"""

from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass, fields

import numpy as np
import torch

from models import autoencoder, pca, var


@dataclass(frozen=True)
class FitArguments:
    """What `models.autoencoder.fit` is called with, and the seed set before it."""

    epochs: int
    batch: int
    rate: float
    improvement: float
    patience: int
    seed: int


def _under(prefix, weights, name):
    """The tensors of `weights` named under `prefix`, with the prefix taken off."""
    tensors = {key[len(prefix):]: tensor for key, tensor in weights.items()
               if key.startswith(prefix)}
    if not tensors:
        raise ValueError(f"the checkpoint holds no {name}")
    return tensors


@dataclass(frozen=True)
class Pca:
    """Principal components, solved rather than trained."""

    MODEL = "pca"
    k: int

    @property
    def prefix(self):
        return f"pca.k{self.k}."

    @property
    def name(self):
        return f"pca k={self.k}"

    def fit(self, rows):
        """Its tensors, how it scores rows, and no losses, since it is solved."""
        space = pca.subspace(rows, self.k)
        # safetensors refuses the transposed view subspace returns
        return ({f"{self.prefix}centre": torch.from_numpy(space.centre),
                 f"{self.prefix}basis": torch.from_numpy(space.basis).contiguous()},
                lambda scored: pca.residuals(scored, space), None)

    def scorer(self, weights, signals):
        """Take this model's `centre` and `basis` out of `weights`, and score with them.

        `weights` is what a run's `weights.safetensors` holds, every model's tensors
        together. What comes back scores rows.
        """
        tensors = _under(self.prefix, weights, self.name)
        space = pca.Subspace(tensors["centre"].numpy(), tensors["basis"].numpy())
        return lambda scored: pca.residuals(scored, space)


@dataclass(frozen=True)
class Var:
    """A vector autoregression of a window's last row on the `rows` - 1 rows before it,
    solved rather than trained."""

    MODEL = "var"
    rows: int

    @property
    def prefix(self):
        return f"var.r{self.rows}."

    @property
    def name(self):
        return f"var r={self.rows}"

    def fit(self, windows):
        """Its tensors, how it scores windows, and no losses, since it is solved."""
        fitted = var.autoregression(windows)
        return ({f"{self.prefix}coefficients":
                 torch.from_numpy(fitted.coefficients).contiguous(),
                 f"{self.prefix}intercept": torch.from_numpy(fitted.intercept)},
                lambda scored: var.residuals(scored, fitted), None)

    def scorer(self, weights, signals):
        """Take this model's `coefficients` and `intercept` out of `weights`, and score
        windows with them."""
        tensors = _under(self.prefix, weights, self.name)
        fitted = var.Autoregression(tensors["coefficients"].numpy(),
                                    tensors["intercept"].numpy())
        return lambda scored: var.residuals(scored, fitted)


class _Autoencoder:
    """What both autoencoders do the same way."""

    def fit(self, rows):
        """Its tensors, how it scores rows, and its mean loss on them each epoch."""
        torch.manual_seed(self.arguments.seed)
        net = self._network(rows.shape[1])
        losses = autoencoder.fit(rows, net, epochs=self.arguments.epochs,
                                 batch=self.arguments.batch, rate=self.arguments.rate,
                                 threshold=self.arguments.improvement,
                                 patience=self.arguments.patience)
        return ({f"{self.prefix}{key}": tensor
                 for key, tensor in net.state_dict().items()},
                lambda scored: autoencoder.residuals(scored, net, rows.shape[1]),
                losses)

    def network_with_weights(self, weights, signals):
        """This model as a network, holding the tensors `weights` kept for it."""
        net = self._network(signals)
        net.load_state_dict(_under(self.prefix, weights, self.name))
        return net

    def scorer(self, weights, signals):
        """Take this model's tensors out of `weights` and score rows with them."""
        net = self.network_with_weights(weights, signals)
        return lambda scored: autoencoder.residuals(scored, net, signals)


@dataclass(frozen=True)
class LinearAe(_Autoencoder):
    """One linear layer down to `k` and one back."""

    MODEL = "linear ae"
    k: int
    arguments: FitArguments

    @property
    def prefix(self):
        return f"linear_ae.k{self.k}."

    @property
    def name(self):
        return f"linear ae k={self.k}"

    def _network(self, signals):
        return autoencoder.LinearAutoencoder(signals=signals, latent_dim=self.k)


@dataclass(frozen=True)
class NonlinearAe(_Autoencoder):
    """A hidden layer of `hidden` units with ReLU on each side of `k`."""

    MODEL = "nonlinear ae"
    C_NAME = "instant_model"                # what the board's C code for it is named
    k: int
    hidden: int
    arguments: FitArguments

    @property
    def prefix(self):
        return f"nonlinear_ae.h{self.hidden}.k{self.k}."

    @property
    def name(self):
        return f"nonlinear ae h={self.hidden} k={self.k}"

    @property
    def onnx_name(self):
        """The name its ONNX files start with."""
        return f"nonlinear_ae_k{self.k}_h{self.hidden}"

    def _network(self, signals):
        return autoencoder.NonlinearAutoencoder(signals=signals, latent_dim=self.k,
                                                hidden=self.hidden)


@dataclass(frozen=True)
class WindowNonlinearAe:
    """The network of `NonlinearAe` on a window of `rows` rows, laid out oldest first as
    one row of `rows` × signals values. It scores a window by the error on its last
    row."""

    MODEL = "window nonlinear ae"
    C_NAME = "window_model"                 # what the board's C code for it is named
    rows: int
    k: int
    hidden: int
    arguments: FitArguments

    @property
    def prefix(self):
        return f"window_nonlinear_ae.r{self.rows}.h{self.hidden}.k{self.k}."

    @property
    def name(self):
        return f"window nonlinear ae r={self.rows} h={self.hidden} k={self.k}"

    @property
    def onnx_name(self):
        """The name its ONNX files start with."""
        return f"window_nonlinear_ae_r{self.rows}_k{self.k}_h{self.hidden}"

    def _network(self, signals):
        return autoencoder.NonlinearAutoencoder(signals=self.rows * signals,
                                                latent_dim=self.k, hidden=self.hidden)

    def flat(self, windows):
        """Each window of shape (rows, signals) as one row, its oldest row first."""
        return windows.reshape(len(windows), -1)

    def fit(self, windows):
        """Its tensors, how it scores windows, and its mean loss on them each epoch."""
        torch.manual_seed(self.arguments.seed)
        net = self._network(windows.shape[2])
        losses = autoencoder.fit(self.flat(windows), net, epochs=self.arguments.epochs,
                                 batch=self.arguments.batch, rate=self.arguments.rate,
                                 threshold=self.arguments.improvement,
                                 patience=self.arguments.patience)
        return ({f"{self.prefix}{key}": tensor
                 for key, tensor in net.state_dict().items()},
                lambda scored: autoencoder.residuals(self.flat(scored), net,
                                                     windows.shape[2]), losses)

    def network_with_weights(self, weights, signals):
        """This model as a network, holding the tensors `weights` kept for it. `signals`
        is how many values a row holds."""
        net = self._network(signals)
        net.load_state_dict(_under(self.prefix, weights, self.name))
        return net

    def scorer(self, weights, signals):
        """Take this model's tensors out of `weights` and score windows with them."""
        net = self.network_with_weights(weights, signals)
        return lambda scored: autoencoder.residuals(self.flat(scored), net, signals)


@dataclass(frozen=True)
class WindowDeltaAe(WindowNonlinearAe):
    """`WindowNonlinearAe` on the steps between the rows of a window, each signal's step
    divided by its std over the windows it is fitted on. It scores a window by the error
    on its last step.

    It is fitted on one window every `stride` rows, and scored on every window."""

    MODEL = "window delta ae"
    stride: int = 1

    @property
    def prefix(self):
        return f"window_delta_ae.r{self.rows}.s{self.stride}.h{self.hidden}.k{self.k}."

    @property
    def name(self):
        return (f"window delta ae r={self.rows} s={self.stride} h={self.hidden} "
                f"k={self.k}")

    @property
    def onnx_name(self):
        """The name its ONNX files start with."""
        return f"window_delta_ae_r{self.rows}_s{self.stride}_k{self.k}_h{self.hidden}"

    def _network(self, signals):
        return autoencoder.DeltaAutoencoder(rows=self.rows, signals=signals,
                                            latent_dim=self.k, hidden=self.hidden)

    def _scale(self, net, windows):
        """Give `net` the std each signal's step has over `windows`."""
        std = np.diff(windows, axis=1).std(axis=(0, 1))
        std[std == 0] = 1.0                   # a constant signal stays at 0
        net.step_std.copy_(torch.from_numpy(std.astype(np.float32)))

    def fit(self, windows):
        """Its tensors, how it scores windows, and its mean loss on them each epoch."""
        torch.manual_seed(self.arguments.seed)
        net = self._network(windows.shape[2])
        self._scale(net, windows)
        losses = autoencoder.fit(self.flat(windows), net, epochs=self.arguments.epochs,
                                 batch=self.arguments.batch, rate=self.arguments.rate,
                                 threshold=self.arguments.improvement,
                                 patience=self.arguments.patience)
        return ({f"{self.prefix}{key}": tensor
                 for key, tensor in net.state_dict().items()},
                lambda scored: autoencoder.residuals(self.flat(scored), net,
                                                     windows.shape[2]), losses)


@dataclass(frozen=True)
class WindowDriftAe(WindowDeltaAe):
    """`WindowDeltaAe` on how far each row of a window sits from its first row rather
    than on the steps, each value divided by its std for its row and signal over the
    windows it is fitted on. It scores a window by the error on how far its last row
    sits from its first."""

    MODEL = "window drift ae"

    @property
    def prefix(self):
        return f"window_drift_ae.r{self.rows}.s{self.stride}.h{self.hidden}.k{self.k}."

    @property
    def name(self):
        return (f"window drift ae r={self.rows} s={self.stride} h={self.hidden} "
                f"k={self.k}")

    @property
    def onnx_name(self):
        """The name its ONNX files start with."""
        return f"window_drift_ae_r{self.rows}_s{self.stride}_k{self.k}_h{self.hidden}"

    def _network(self, signals):
        return autoencoder.DriftAutoencoder(rows=self.rows, signals=signals,
                                            latent_dim=self.k, hidden=self.hidden)

    def _scale(self, net, windows):
        """Give `net` the std each row's drift from the first has over `windows`."""
        std = (windows[:, 1:] - windows[:, :1]).std(axis=0)
        std[std == 0] = 1.0                   # a constant signal stays at 0
        net.drift_std.copy_(torch.from_numpy(std.astype(np.float32)))


@dataclass(frozen=True)
class WindowConv1dAe(WindowDeltaAe):
    """`WindowDeltaAe` with 1D convolutions along time in place of dense layers. `k` is
    the channels at its narrowest, `hidden` those of the convolution before."""

    MODEL = "window conv1d ae"

    @property
    def prefix(self):
        return f"window_conv1d_ae.r{self.rows}.s{self.stride}.h{self.hidden}.k{self.k}."

    @property
    def name(self):
        return (f"window conv1d ae r={self.rows} s={self.stride} h={self.hidden} "
                f"k={self.k}")

    @property
    def onnx_name(self):
        """The name its ONNX files start with."""
        return f"window_conv1d_ae_r{self.rows}_s{self.stride}_k{self.k}_h{self.hidden}"

    def _network(self, signals):
        return autoencoder.Conv1dAutoencoder(rows=self.rows, signals=signals,
                                             latent_dim=self.k, hidden=self.hidden)


MODELS = {model.MODEL: model
          for model in (Pca, Var, LinearAe, NonlinearAe, WindowNonlinearAe,
                        WindowDeltaAe, WindowDriftAe, WindowConv1dAe)}
ARGUMENTS = tuple(field.name for field in fields(FitArguments))


def as_dict(model):
    """What a run writes down of a model, in its `inputs` and beside its threshold."""
    kept = asdict(model)
    arguments = kept.pop("arguments", {})
    return {"model": model.MODEL, **kept, **arguments}


def model_from(kept):
    """The model `as_dict` wrote down."""
    kept = dict(kept)
    model = MODELS[kept.pop("model")]
    arguments = {name: kept.pop(name) for name in ARGUMENTS if name in kept}
    if model in (Pca, Var):
        return model(**kept)
    return model(**kept, arguments=FitArguments(**arguments))


def _spread(kept):
    """Each way of taking one value out of every list `kept` holds."""
    listed = [(name, value) for name, value in kept.items() if isinstance(value, list)]
    fixed = {name: value for name, value in kept.items() if not isinstance(value, list)}
    for picked in itertools.product(*(values for _, values in listed)):
        yield {**fixed, **dict(zip((name for name, _ in listed), picked))}


def models_from(listed):
    """The models `listed` asks for, a list value standing for one model per value."""
    return [model_from(kept) for entry in listed for kept in _spread(entry)]
