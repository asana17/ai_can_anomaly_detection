"""The models a run fits, each knowing how it is fitted, named and built back.

Training fits a model here and keeps its tensors. Anything that scores rows later
takes the same model's tensors back out. `as_dict` and `model_from` are how one model is
written down and read back, `models_from` how a list of them is asked for.
"""

from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass, fields

import torch

from models import autoencoder, pca


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
        return f"rules + pca k={self.k}"

    def fit(self, rows):
        """Its tensors, how it scores rows, and no losses, since it is solved."""
        space = pca.subspace(rows, self.k)
        # safetensors refuses the transposed view subspace returns
        return ({f"{self.prefix}centre": torch.from_numpy(space.centre),
                 f"{self.prefix}basis": torch.from_numpy(space.basis).contiguous()},
                lambda scored: pca.residuals(scored, space), None)

    def load(self, weights, signals):
        """Take this model's `centre` and `basis` out of `weights`, and score with them.

        `weights` is what a run's `weights.safetensors` holds, every model's tensors
        together. What comes back scores rows.
        """
        tensors = _under(self.prefix, weights, self.name)
        space = pca.Subspace(tensors["centre"].numpy(), tensors["basis"].numpy())
        return lambda scored: pca.residuals(scored, space)


class _Autoencoder:
    """What both autoencoders do the same way."""

    def fit(self, rows):
        """Its tensors, how it scores rows, and its mean loss on them each epoch."""
        torch.manual_seed(self.arguments.seed)
        net = self.network(rows.shape[1])
        losses = autoencoder.fit(rows, net, epochs=self.arguments.epochs,
                                 batch=self.arguments.batch, rate=self.arguments.rate,
                                 threshold=self.arguments.improvement,
                                 patience=self.arguments.patience)
        return ({f"{self.prefix}{key}": tensor
                 for key, tensor in net.state_dict().items()},
                lambda scored: autoencoder.residuals(scored, net), losses)

    def load(self, weights, signals):
        """Take this model's tensors out of `weights` and put them in a network.

        `weights` is what a run's `weights.safetensors` holds, every model's tensors
        together. The network is built at this model's shape, and what comes back
        scores rows.
        """
        net = self.network(signals)
        net.load_state_dict(_under(self.prefix, weights, self.name))
        return lambda scored: autoencoder.residuals(scored, net)


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
        return f"rules + linear ae k={self.k}"

    def network(self, signals):
        return autoencoder.LinearAutoencoder(signals=signals, latent_dim=self.k)


@dataclass(frozen=True)
class NonlinearAe(_Autoencoder):
    """A hidden layer of `hidden` units with ReLU on each side of `k`."""

    MODEL = "nonlinear ae"
    k: int
    hidden: int
    arguments: FitArguments

    @property
    def prefix(self):
        return f"nonlinear_ae.h{self.hidden}.k{self.k}."

    @property
    def name(self):
        return f"rules + nonlinear ae h={self.hidden} k={self.k}"

    def network(self, signals):
        return autoencoder.NonlinearAutoencoder(signals=signals, latent_dim=self.k,
                                                hidden=self.hidden)


MODELS = {model.MODEL: model for model in (Pca, LinearAe, NonlinearAe)}
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
    if model is Pca:
        return Pca(**kept)
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
