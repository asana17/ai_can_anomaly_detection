import numpy as np
import onnxruntime
import pytest
import torch
from safetensors.torch import save_file

from board.export import fits_in, load, write
from models.autoencoder import NonlinearAutoencoder


def _model():
    torch.manual_seed(0)
    return NonlinearAutoencoder(signals=17, latent_dim=4, hidden=8)


def _rows(n=512):
    return np.random.default_rng(0).normal(size=(n, 17)).astype(np.float32)


def _run(tmp_path, model):
    save_file({f"nonlinear_ae.h8.k4.{n}": t for n, t in model.state_dict().items()},
              str(tmp_path / "weights.safetensors"))
    return str(tmp_path)


def _outputs(path, rows):
    session = onnxruntime.InferenceSession(path, providers=["CPUExecutionProvider"])
    return session.run(None, {"row": rows})[0]


def test_load_gives_back_the_fit_the_run_saved(tmp_path):
    model = _model()
    state = load(_run(tmp_path, model), k=4, h=8)
    assert all(torch.equal(state[n], t) for n, t in model.state_dict().items())


def test_load_refuses_a_fit_the_run_does_not_hold(tmp_path):
    with pytest.raises(ValueError):
        load(_run(tmp_path, _model()), k=4, h=16)


def test_the_float_file_reconstructs_like_the_model(tmp_path):
    model, rows = _model(), _rows()
    write([("ae", model)], rows, str(tmp_path / "out"), batch=128)
    expected = model(torch.from_numpy(rows)).detach().numpy()
    assert np.allclose(_outputs(str(tmp_path / "out" / "ae_float.onnx"), rows), expected,
                       atol=1e-5)


def test_the_int8_file_runs_on_the_same_rows(tmp_path):
    rows = _rows()
    write([("ae", _model())], rows, str(tmp_path / "out"), batch=128)
    assert _outputs(str(tmp_path / "out" / "ae_int8.onnx"), rows).shape == rows.shape


def test_only_the_float_and_int8_files_are_kept(tmp_path):
    write([("ae", _model())], _rows(), str(tmp_path / "out"), batch=128)
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [
        "ae_float.onnx", "ae_int8.onnx"]


def test_every_model_asked_for_is_written(tmp_path):
    rows = _rows()
    write([("one", _model()), ("two", _model())], rows, str(tmp_path / "out"), batch=128)
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [
        "one_float.onnx", "one_int8.onnx", "two_float.onnx", "two_int8.onnx"]


def test_every_fit_a_run_saved_is_listed(tmp_path):
    save_file({**{f"nonlinear_ae.h8.k4.{n}": t
                  for n, t in _model().state_dict().items()},
               **{f"nonlinear_ae.h32.k2.{n}": t
                  for n, t in _model().state_dict().items()},
               "pca.k4.centre": torch.zeros(17)},
              str(tmp_path / "weights.safetensors"))
    assert fits_in(str(tmp_path)) == [(2, 32), (4, 8)]


def test_write_never_overwrites_an_export(tmp_path):
    dest = tmp_path / "out"
    dest.mkdir()
    (dest / "ae_float.onnx").write_text("kept")
    with pytest.raises(FileExistsError):
        write([("ae", _model())], _rows(), str(dest), batch=128)
    assert (dest / "ae_float.onnx").read_text() == "kept"
