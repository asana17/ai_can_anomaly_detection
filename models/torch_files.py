"""How rows are scored with a model in torch, on the weights of a fit."""

from __future__ import annotations

from preprocess.features.scale import Scale


def scale_of(weights):
    """The scale the rows of a fit were z-scored with, kept in its `weights`."""
    return Scale(weights["scale.mean"].numpy(), weights["scale.std"].numpy())


def torch_scorer(weights):
    """What scores rows with a model in torch, on `weights` of a fit."""
    # the scale is fitted on every signal a row holds
    signals = weights["scale.mean"].shape[0]
    return lambda model: model.scorer(weights, signals)
