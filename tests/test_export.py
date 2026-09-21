import json
import os

import numpy as np
import onnxruntime
import torch

from deploy import export
from deploy.export import write_onnx_files
from models.autoencoder import NonlinearAutoencoder

REVISION = "ab" * 20
COMMIT = "de" * 20

NONLINEAR = {"model": "nonlinear ae", "k": 4, "hidden": 8, "epochs": 1, "batch": 128,
             "rate": 0.001, "improvement": 0.0, "patience": 1, "seed": 0}


def _model():
    torch.manual_seed(0)
    return NonlinearAutoencoder(signals=17, latent_dim=4, hidden=8)


def _rows(n=512):
    return np.random.default_rng(0).normal(size=(n, 17)).astype(np.float32)


def _outputs(path, rows):
    session = onnxruntime.InferenceSession(path, providers=["CPUExecutionProvider"])
    return session.run(None, {"row": rows})[0]


def test_the_float_file_reconstructs_like_the_model(tmp_path):
    model, rows = _model(), _rows()
    write_onnx_files([("ae", model)], 17, str(tmp_path / "out"))
    expected = model(torch.from_numpy(rows)).detach().numpy()
    assert np.allclose(_outputs(str(tmp_path / "out" / "ae_float.onnx"), rows), expected,
                       atol=1e-5)


def test_only_the_float_file_is_kept(tmp_path):
    write_onnx_files([("ae", _model())], 17, str(tmp_path / "out"))
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == ["ae_float.onnx"]


def test_every_model_asked_for_is_written(tmp_path):
    write_onnx_files([("one", _model()), ("two", _model())], 17, str(tmp_path / "out"))
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [
        "one_float.onnx", "two_float.onnx"]


def fitted(monkeypatch, model):
    """A stand-in models directory holding `model` at k=4 h=8, and a PCA beside it."""
    weights = {f"nonlinear_ae.h8.k4.{name}": tensor
               for name, tensor in model.state_dict().items()}
    weights.update({"scale.mean": torch.zeros(17), "scale.std": torch.ones(17),
                    "pca.k2.centre": torch.zeros(17),
                    "pca.k2.basis": torch.zeros(17, 2)})
    where = {"repo": "u/d", "revision": REVISION, "path": "train_sets/20260101-000000"}
    meta = {"inputs": {"train_set": "train_sets/20260101-000000",
                       "models": [{"model": "pca", "k": 2}, NONLINEAR]},
            "train_set": where, "split": dict(where, path="splits/20260101-000000"),
            "grid": dict(where, path="grids/20260101-000000"), "min_speed": 5.0}
    monkeypatch.setattr(export, "fetch_fitted_models", lambda *args: (weights, meta))


def test_every_nonlinear_autoencoder_of_the_fit_is_written(tmp_path, hub, monkeypatch):
    model, rows = _model(), _rows()
    fitted(monkeypatch, model)
    made = export.main("u/runs", COMMIT, "models/20260101-000000", str(tmp_path))

    folder = tmp_path / made["path"]
    assert made["path"].startswith("onnx/")
    assert sorted(os.listdir(folder)) == ["meta.json", "nonlinear_ae_k4_h8_float.onnx"]
    expected = model(torch.from_numpy(rows)).detach().numpy()
    assert np.allclose(_outputs(str(folder / "nonlinear_ae_k4_h8_float.onnx"), rows),
                       expected, atol=1e-5)
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"models": "models/20260101-000000"}
    assert meta["models"] == {"repo": "u/runs", "revision": COMMIT,
                              "path": "models/20260101-000000"}
    assert meta["exported"] == [NONLINEAR]

