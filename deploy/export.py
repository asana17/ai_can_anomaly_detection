"""Write every nonlinear autoencoder of a fit out as float ONNX, and keep them.

    python3 -m deploy.export runs_repo revision models/<time> runs_dir [--rebuild]
"""

from __future__ import annotations

import os
import platform

import numpy as np
import onnx
import torch

from common.cli import arguments
from common.hub_dirs import reuse_or_make
from evaluate.fit import fetch_models
from models.fits import NonlinearAe, as_dict, models_from
from models.onnx_files import onnx_name


def write_onnx_files(models, signals, dest):
    """Write each model into `dest` as float ONNX, reading rows of `signals` values."""
    os.makedirs(dest, exist_ok=True)
    for name, model in models:
        model.eval()
        torch.onnx.export(model, torch.zeros(1, signals),
                          os.path.join(dest, f"{name}_float.onnx"), dynamo=False,
                          input_names=["row"], output_names=["out"],
                          dynamic_axes={"row": {0: "batch"}, "out": {0: "batch"}})


def write_export(folder, runs_repo, revision, models_path, runs_dir):
    """Write each nonlinear autoencoder of a fit as float ONNX, and return what to record."""
    weights, models_meta = fetch_models(runs_repo, revision, models_path, runs_dir)
    # the scale is fitted on every signal a row holds
    signals = weights["scale.mean"].shape[0]

    # the board runs a nonlinear autoencoder, so the other models are left out
    wanted = [model for model in models_from(models_meta["inputs"]["models"])
              if isinstance(model, NonlinearAe)]
    write_onnx_files([(onnx_name(model), model.network_with_weights(weights, signals))
                      for model in wanted], signals, folder)
    return {"models": {"repo": runs_repo, "revision": revision, "path": models_path},
            **{name: models_meta[name] for name in ("train_set", "split", "grid")},
            "exported": [as_dict(model) for model in wanted],
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "onnx": onnx.__version__}}


def main(runs_repo, revision, models_path, runs_dir, rebuild=False):
    inputs = {"models": models_path}
    return reuse_or_make(runs_repo, "onnx", inputs, runs_dir,
                         lambda folder: write_export(folder, runs_repo, revision,
                                                     models_path, runs_dir),
                         rebuild)


if __name__ == "__main__":
    main(**arguments(("runs_repo", "revision", "models_path", "runs_dir"),
                    rebuild=False))
