"""Write every window nonlinear autoencoder of a window fit out as float ONNX, and keep
them.

    python3 -m deploy.export_windows runs_repo revision window_models/<time> runs_dir [--rebuild]
"""

from __future__ import annotations

import platform

import numpy as np
import onnx
import torch

from common.cli import arguments
from common.hub_dirs import reuse_or_make
from deploy.export import write_onnx_files
from models.fit import fetch_fitted_models
from models.fits import WindowNonlinearAe, as_dict, models_from


def write_export(folder, runs_repo, revision, models_path, runs_dir):
    """Write each window nonlinear autoencoder of a window fit as float ONNX, and return
    what to record."""
    weights, models_meta = fetch_fitted_models(runs_repo, revision, models_path,
                                               runs_dir)
    # the scale is fitted on every signal a row holds
    signals = weights["scale.mean"].shape[0]

    # the board runs a network, so the vector autoregressions are left out
    wanted = [model for model in models_from(models_meta["inputs"]["models"])
              if isinstance(model, WindowNonlinearAe)]
    for model in wanted:
        # a window goes in as one row, its oldest row first
        net = model.network_with_weights(weights, signals)
        write_onnx_files([(model.onnx_name, net)], model.rows * signals, folder)
    return {"models": {"repo": runs_repo, "revision": revision, "path": models_path},
            **{name: models_meta[name] for name in ("train_set", "log_split", "grid")},
            "exported": [as_dict(model) for model in wanted],
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "onnx": onnx.__version__}}


def main(runs_repo, revision, models_path, runs_dir, rebuild=False, dry_run=False):
    return reuse_or_make(runs_repo, "window_onnx", {"models": models_path}, {}, runs_dir,
                         lambda folder: write_export(folder, runs_repo, revision,
                                                     models_path, runs_dir),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("runs_repo", "revision", "models_path", "runs_dir"),
                    rebuild=False))
