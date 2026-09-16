import json

import numpy as np
import torch
from safetensors.torch import save_file

from board.export import write
from evaluate.board.compare import onnx_residuals, sources_for, threshold_for
from evaluate.counting import detection
from evaluate.pc.run import Settings
from models.autoencoder import NonlinearAutoencoder, residuals


def _model():
    torch.manual_seed(0)
    return NonlinearAutoencoder(signals=17, latent_dim=4, hidden=8)


def _rows(n=512):
    return np.random.default_rng(0).normal(size=(n, 17)).astype(np.float32)


def _export(tmp_path, model, rows):
    run = tmp_path / "results" / "20260101-000000"
    run.mkdir(parents=True)
    save_file({f"nonlinear_ae.h8.k4.{n}": t for n, t in model.state_dict().items()},
              str(run / "weights.safetensors"))
    dest = tmp_path / "board" / "20260101-010000"
    write(model, rows, str(dest), "nonlinear_ae_k4_h8", batch=128)
    (dest / "meta.json").write_text(json.dumps(
        {"run": "results/20260101-000000", "k": 4, "h": 8}))
    return "20260101-010000"


def _test_set(scores, hours=1.0):
    """A test set of `scores` rows, one attack on the first two, nothing else on."""
    n = len(scores)
    return {"rows": np.zeros((n, 17), dtype=np.float32), "seg": np.zeros(n, dtype=int),
            "mv": np.ones(n, dtype=bool), "quiet": np.arange(n) >= 2,
            "attacks": [{"first": 0, "last": 1}],
            "rules": np.zeros(n, dtype=bool),
            "scored": np.ones(1, dtype=bool), "hours": hours}


def test_the_fit_scores_the_rows_it_was_saved_from(tmp_path):
    model, rows = _model(), _rows()
    _export(tmp_path, model, rows)
    _, sources = sources_for(str(tmp_path), "20260101-010000", 17)
    assert np.allclose(sources["torch"](rows), residuals(rows, model))


def test_the_int8_file_scores_every_row(tmp_path):
    rows = _rows()
    _export(tmp_path, _model(), rows)
    _, sources = sources_for(str(tmp_path), "20260101-010000", 17)
    assert sources["int8"](rows).shape == (len(rows),)


def test_the_threshold_cuts_off_the_target_share():
    scores = np.arange(1000, dtype=np.float32)
    assert (scores > threshold_for(scores, 0.01)).sum() == 10


def test_an_attack_is_found_when_a_row_of_it_is_flagged():
    flag = np.zeros(100, dtype=bool)
    flag[1] = True
    got = detection(flag, _test_set(flag), Settings())
    assert [c["found"] for c in got] == [1, 0]      # one row cannot hold for ten


def test_a_model_that_flags_nothing_finds_nothing():
    flag = np.zeros(100, dtype=bool)
    got = detection(flag, _test_set(flag), Settings())
    assert [c["found"] for c in got] == [0, 0]


def test_alarms_outside_an_attack_are_counted_by_the_hour():
    flag = np.zeros(100, dtype=bool)
    flag[50:60] = True
    got = detection(flag, _test_set(flag, hours=2.0), Settings())
    assert [c["alarms_per_hour"] for c in got] == [0.5, 0.5]


def test_onnx_residuals_reads_the_rows_it_is_given(tmp_path):
    model, rows = _model(), _rows()
    write(model, rows, str(tmp_path / "out"), "ae", batch=128)
    got = onnx_residuals(str(tmp_path / "out" / "ae_float.onnx"), rows[:8])
    assert np.allclose(got, residuals(rows[:8], model), atol=1e-6)
