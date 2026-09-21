import json
import os

import numpy as np
import torch

from deploy import quantize
from deploy.export import write_onnx_files
from deploy.quantize import write_int8_files
from models.autoencoder import NonlinearAutoencoder, residuals
from models.onnx_files import onnx_residuals
from preprocess.features.scale import Scale
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20
COMMIT = "de" * 20

ENTRY = {"model": "nonlinear ae", "k": 4, "hidden": 8, "epochs": 1, "batch": 128,
         "rate": 0.001, "improvement": 0.0, "patience": 1, "seed": 0}


def _model():
    torch.manual_seed(0)
    return NonlinearAutoencoder(signals=17, latent_dim=4, hidden=8)


def _rows(n=512):
    return np.random.default_rng(0).normal(size=(n, 17)).astype(np.float32)


def _quantized(tmp_path, model, rows):
    source, dest = str(tmp_path / "onnx"), str(tmp_path / "quantize")
    write_onnx_files([("nonlinear_ae_k4_h8", model)], 17, source)
    write_int8_files(["nonlinear_ae_k4_h8"], source, rows, dest, batch=128)
    return dest


def test_the_int8_file_runs_on_the_same_rows(tmp_path):
    rows = _rows()
    dest = _quantized(tmp_path, _model(), rows)
    assert onnx_residuals(f"{dest}/nonlinear_ae_k4_h8_int8.onnx", rows).shape == (
        len(rows),)


def test_only_the_int8_file_is_kept(tmp_path):
    dest = _quantized(tmp_path, _model(), _rows())
    assert sorted(p.name for p in (tmp_path / "quantize").iterdir()) == [
        "nonlinear_ae_k4_h8_int8.onnx"]


def test_onnx_residuals_reads_the_rows_it_is_given(tmp_path):
    model, rows = _model(), _rows()
    write_onnx_files([("ae", model)], 17, str(tmp_path / "out"))
    got = onnx_residuals(str(tmp_path / "out" / "ae_float.onnx"), rows[:8])
    assert np.allclose(got, residuals(rows[:8], model), atol=1e-6)


def exported(monkeypatch, tmp_path):
    """A stand-in export of one float file, from a train set of moving rows."""
    signals = len(SIGNALS)
    torch.manual_seed(0)
    source = str(tmp_path / "source")
    write_onnx_files([("nonlinear_ae_k4_h8", NonlinearAutoencoder(
        signals=signals, latent_dim=4, hidden=8))], signals, source)
    where = {"repo": "u/d", "revision": REVISION, "path": "train_sets/20260101-000000"}
    meta = {"models": {"repo": "u/runs", "revision": REVISION,
                       "path": "models/20260101-000000"},
            "train_set": where, "split": dict(where, path="splits/20260101-000000"),
            "grid": dict(where, path="grids/20260101-000000"), "exported": [ENTRY]}
    monkeypatch.setattr(quantize, "read_dir", lambda *args: (source, meta))
    raw = np.random.default_rng(0).normal(size=(256, signals)).astype(np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = 10.0
    monkeypatch.setattr(quantize, "fetch_train_set", lambda *args: {
        "train": raw, "calibration": raw, "min_speed": 5.0,
        "scale": Scale(np.zeros(signals, np.float32), np.ones(signals, np.float32))})


def test_every_float_file_of_the_export_is_quantized(tmp_path, hub, monkeypatch):
    exported(monkeypatch, tmp_path)
    made = quantize.main("u/runs", COMMIT, "onnx/20260101-000000", str(tmp_path),
                         str(tmp_path))

    folder = tmp_path / made["path"]
    assert made["path"].startswith("quantize/")
    assert sorted(os.listdir(folder)) == ["meta.json", "nonlinear_ae_k4_h8_int8.onnx"]
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"onnx": "onnx/20260101-000000"}
    assert meta["onnx"] == {"repo": "u/runs", "revision": COMMIT,
                            "path": "onnx/20260101-000000"}
    assert meta["models"]["path"] == "models/20260101-000000"
