import numpy as np
import onnxruntime
import torch

from quantize.export import write_onnx_files
from models.autoencoder import NonlinearAutoencoder


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
    write_onnx_files([("ae", model)], rows, str(tmp_path / "out"), batch=128)
    expected = model(torch.from_numpy(rows)).detach().numpy()
    assert np.allclose(_outputs(str(tmp_path / "out" / "ae_float.onnx"), rows), expected,
                       atol=1e-5)


def test_the_int8_file_runs_on_the_same_rows(tmp_path):
    rows = _rows()
    write_onnx_files([("ae", _model())], rows, str(tmp_path / "out"), batch=128)
    assert _outputs(str(tmp_path / "out" / "ae_int8.onnx"), rows).shape == rows.shape


def test_only_the_float_and_int8_files_are_kept(tmp_path):
    write_onnx_files([("ae", _model())], _rows(), str(tmp_path / "out"), batch=128)
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [
        "ae_float.onnx", "ae_int8.onnx"]


def test_every_model_asked_for_is_written(tmp_path):
    rows = _rows()
    write_onnx_files([("one", _model()), ("two", _model())], rows, str(tmp_path / "out"), batch=128)
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [
        "one_float.onnx", "one_int8.onnx", "two_float.onnx", "two_int8.onnx"]
