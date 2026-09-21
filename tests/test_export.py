import numpy as np
import onnxruntime
import torch

from deploy.export import write_onnx_files
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
