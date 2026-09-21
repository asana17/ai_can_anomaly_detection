import numpy as np
import torch

from deploy.export import write_onnx_files
from deploy.quantize import (int8_thresholds, onnx_residuals, threshold_for,
                             write_int8_files)
from models.autoencoder import NonlinearAutoencoder, residuals

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


def test_each_int8_file_gets_a_threshold_beside_its_model(tmp_path):
    rows = _rows()
    dest = _quantized(tmp_path, _model(), rows)
    got = int8_thresholds([ENTRY], rows, dest, 0.01)
    scores = onnx_residuals(f"{dest}/nonlinear_ae_k4_h8_int8.onnx", rows)
    assert got[0] == {**ENTRY, "int8_threshold": threshold_for(scores, 0.01)}


def test_the_threshold_cuts_off_the_target_share():
    scores = np.arange(1000, dtype=np.float32)
    assert (scores > threshold_for(scores, 0.01)).sum() == 10


def test_onnx_residuals_reads_the_rows_it_is_given(tmp_path):
    model, rows = _model(), _rows()
    write_onnx_files([("ae", model)], 17, str(tmp_path / "out"))
    got = onnx_residuals(str(tmp_path / "out" / "ae_float.onnx"), rows[:8])
    assert np.allclose(got, residuals(rows[:8], model), atol=1e-6)
