import json
import os

import numpy as np
import onnxruntime
import torch

from deploy import export_windows
from models.autoencoder import NonlinearAutoencoder

COMMIT = "de" * 20

WINDOW = {"model": "window nonlinear ae", "rows": 3, "k": 4, "hidden": 8, "epochs": 1,
          "batch": 128, "rate": 0.001, "improvement": 0.0, "patience": 1, "seed": 0}


def fitted(monkeypatch, model):
    """A stand-in window models directory holding `model` at rows=3 k=4 h=8, and a VAR
    listed beside it."""
    weights = {f"window_nonlinear_ae.r3.h8.k4.{name}": tensor
               for name, tensor in model.state_dict().items()}
    weights.update({"scale.mean": torch.zeros(17), "scale.std": torch.ones(17)})
    where = {"repo": "u/d", "revision": "ab" * 20, "path": "train_sets/20260101-000000"}
    meta = {"inputs": {"train_set": "train_sets/20260101-000000",
                       "models": [{"model": "var", "rows": 2}, WINDOW]},
            "train_set": where,
            "calibration_set": dict(where, path="calibration_sets/20260101-000000"),
            "log_split": dict(where, path="log_splits/20260101-000000"),
            "grid": dict(where, path="grids/20260101-000000"), "min_speed": 5.0}
    monkeypatch.setattr(export_windows, "fetch_fitted_models",
                        lambda *args: (weights, meta))


def test_every_window_nonlinear_autoencoder_is_written(tmp_path, hub, monkeypatch):
    torch.manual_seed(0)
    model = NonlinearAutoencoder(signals=3 * 17, latent_dim=4, hidden=8)
    fitted(monkeypatch, model)
    made = export_windows.main("u/runs", COMMIT, "window_models/20260101-000000",
                               str(tmp_path))

    folder = tmp_path / made["path"]
    assert made["path"].startswith("window_onnx/")
    name = "window_nonlinear_ae_r3_k4_h8_float.onnx"
    assert sorted(os.listdir(folder)) == ["meta.json", name]
    windows = np.random.default_rng(0).normal(size=(64, 3 * 17)).astype(np.float32)
    session = onnxruntime.InferenceSession(str(folder / name),
                                           providers=["CPUExecutionProvider"])
    expected = model(torch.from_numpy(windows)).detach().numpy()
    assert np.allclose(session.run(None, {"row": windows})[0], expected, atol=1e-5)
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"models": "window_models/20260101-000000"}
    assert meta["exported"] == [WINDOW]
