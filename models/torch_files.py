"""How rows are scored with a model in torch, on the weights of a fit."""

from __future__ import annotations


def torch_scorer(weights):
    """What scores rows with a model in torch, on `weights` of a fit."""
    # the scale is fitted on every signal a row holds
    signals = weights["scale.mean"].shape[0]
    return lambda model: model.scorer(weights, signals)
