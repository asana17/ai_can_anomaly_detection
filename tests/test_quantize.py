import json
import os

import numpy as np
import pytest
import torch

from deploy import quantize
from deploy.export import write_onnx_files
from deploy.quantize import batch_for, write_int8_files
from common.settings import QuantizeSettings
from models.autoencoder import DriftAutoencoder, NonlinearAutoencoder, residuals
from models.fits import model_from
from models.onnx_files import onnx_residuals
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20
COMMIT = "de" * 20

ENTRY = {"model": "nonlinear ae", "k": 4, "hidden": 8, "epochs": 1,
         "batch": QuantizeSettings().BATCH, "rate": 0.001, "improvement": 0.0,
         "patience": 1, "seed": 0}


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
    assert np.allclose(got, residuals(rows[:8], model, 17), atol=1e-6)


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
            "train_set": where,
            "log_split": dict(where, path="log_splits/20260101-000000"),
            "grid": dict(where, path="grids/20260101-000000"), "exported": [ENTRY]}
    monkeypatch.setattr(quantize, "read_dir", lambda *args: (source, meta))
    monkeypatch.setattr(quantize, "fetch_fitted_models", lambda *args: (
        {"scale.mean": torch.zeros(signals), "scale.std": torch.ones(signals)},
        {"inputs": {"models": [ENTRY]}}))
    raw = np.random.default_rng(0).normal(size=(256, signals)).astype(np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = 10.0
    monkeypatch.setattr(quantize, "fetch_train_set", lambda *args: {
        "train": raw, "calibration": raw, "min_speed": 5.0})
    return raw


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


def test_a_model_fitted_at_another_batch_stops_it():
    settings = QuantizeSettings()
    with pytest.raises(ValueError):
        batch_for([dict(ENTRY, batch=settings.BATCH * 2)], settings)


def test_pca_alone_leaves_the_batch_to_settings():
    settings = QuantizeSettings()
    assert batch_for([{"model": "pca", "k": 4}], settings) == settings.BATCH


def test_a_row_holding_a_nan_is_left_out_of_the_ranges(tmp_path, hub, monkeypatch):
    raw = exported(monkeypatch, tmp_path)
    raw[3, 1] = np.nan
    given = []
    monkeypatch.setattr(quantize, "write_int8_files", lambda names, source, rows,
                        folder, batch: given.append(rows))
    quantize.main("u/runs", COMMIT, "onnx/20260101-000000", str(tmp_path),
                  str(tmp_path))

    assert len(given[0]) == len(raw) - 1 and not np.isnan(given[0]).any()


WINDOW_ENTRY = {"model": "window drift ae", "rows": 3, "k": 4, "hidden": 8, "stride": 2,
                "epochs": 1, "batch": QuantizeSettings().BATCH, "rate": 0.001,
                "improvement": 0.0, "patience": 1, "seed": 0}


def exported_windows(monkeypatch, tmp_path):
    """A stand-in export of one window model, from a train set of moving rows."""
    signals = len(SIGNALS)
    torch.manual_seed(0)
    source = str(tmp_path / "source")
    name = model_from(WINDOW_ENTRY).onnx_name
    write_onnx_files([(name, DriftAutoencoder(rows=3, signals=signals, latent_dim=4,
                                              hidden=8))], 3 * signals, source)
    where = {"repo": "u/d", "revision": REVISION, "path": "train_sets/20260101-000000"}
    meta = {"models": {"repo": "u/runs", "revision": REVISION,
                       "path": "window_models/20260101-000000"},
            "train_set": where,
            "log_split": dict(where, path="log_splits/20260101-000000"),
            "grid": dict(where, path="grids/20260101-000000"),
            "exported": [WINDOW_ENTRY]}
    monkeypatch.setattr(quantize, "read_dir", lambda *args: (source, meta))
    monkeypatch.setattr(quantize, "fetch_fitted_models", lambda *args: (
        {"scale.mean": torch.zeros(signals), "scale.std": torch.ones(signals)},
        {"inputs": {"models": [WINDOW_ENTRY]}}))
    raw = np.random.default_rng(0).normal(size=(40, signals)).astype(np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = 10.0
    monkeypatch.setattr(quantize, "fetch_train_set", lambda *args: {
        "train": raw, "seg": np.repeat([0, 1], 20).astype(np.int32), "min_speed": 5.0})
    return raw, name


def test_every_window_model_of_a_window_export_is_quantized(tmp_path, hub, monkeypatch):
    _, name = exported_windows(monkeypatch, tmp_path)
    made = quantize.main("u/runs", COMMIT, "window_onnx/20260101-000000", str(tmp_path),
                         str(tmp_path))

    folder = tmp_path / made["path"]
    assert made["path"].startswith("window_quantize/")
    assert sorted(os.listdir(folder)) == ["meta.json", f"{name}_int8.onnx"]
    assert json.load(open(folder / "meta.json"))["inputs"] == {
        "onnx": "window_onnx/20260101-000000"}


def test_a_window_model_is_quantized_on_the_windows_it_was_fitted_on(tmp_path, hub,
                                                                     monkeypatch):
    raw, _ = exported_windows(monkeypatch, tmp_path)
    raw[5, 1] = np.nan
    given = []
    monkeypatch.setattr(quantize, "write_int8_file", lambda name, source, batches,
                        folder: given.append(np.concatenate(list(batches))))
    quantize.main("u/runs", COMMIT, "window_onnx/20260101-000000", str(tmp_path),
                  str(tmp_path))

    # rows 2, 4, ... of each 20-row segment end a window. Those holding row 5 are gone
    ends = [end for start in (0, 20) for end in range(start + 2, start + 20, 2)
            if not end - 2 <= 5 <= end]
    assert np.array_equal(given[0], raw[np.array(ends)[:, None] + np.arange(-2, 1)]
                          .reshape(len(ends), -1))
