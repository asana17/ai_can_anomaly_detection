import json

import numpy as np
import torch
from safetensors.torch import save_file

from evaluate.quantize.compare import models_in, sources_for
from quantize.export import onnx_residuals, threshold_for, write
from evaluate.counting import detection
from common.settings import Settings
from models.autoencoder import NonlinearAutoencoder, residuals


def _model():
    torch.manual_seed(0)
    return NonlinearAutoencoder(signals=17, latent_dim=4, hidden=8)


def _rows(n=512):
    return np.random.default_rng(0).normal(size=(n, 17)).astype(np.float32)


def _export(tmp_path, model, rows, meta=None):
    run = tmp_path / "results" / "20260101-000000"
    run.mkdir(parents=True)
    save_file({f"nonlinear_ae.h8.k4.{n}": t for n, t in model.state_dict().items()},
              str(run / "weights.safetensors"))
    dest = tmp_path / "quantize" / "20260101-010000"
    write([("nonlinear_ae_k4_h8", model)], rows, str(dest), batch=128)
    (dest / "meta.json").write_text(json.dumps(
        meta or {"run": "results/20260101-000000", "models": [{"k": 4, "h": 8}]}))
    return "20260101-010000"


def _test_set(scores, hours=1.0):
    """A test set of `scores` rows, one attack on the first two, nothing else on."""
    n = len(scores)
    return {"rows": np.zeros((n, 17), dtype=np.float32), "seg": np.zeros(n, dtype=int),
            "mv": np.ones(n, dtype=bool), "quiet": np.arange(n) >= 2,
            "attacks": [{"first": 0, "last": 1}],
            "rules": np.zeros(n, dtype=bool),
            "scored": np.ones(1, dtype=bool), "hours": hours}


def _sources(tmp_path, exported):
    export_dir = str(tmp_path / "quantize" / exported)
    meta, models = models_in(export_dir)
    k, h = models[0]
    return sources_for(str(tmp_path / meta["run"]), export_dir, k, h, 17)


def test_the_fit_scores_the_rows_it_was_saved_from(tmp_path):
    model, rows = _model(), _rows()
    sources = _sources(tmp_path, _export(tmp_path, model, rows))
    assert np.allclose(sources["torch"](rows), residuals(rows, model))


def test_the_int8_file_scores_every_row(tmp_path):
    rows = _rows()
    sources = _sources(tmp_path, _export(tmp_path, _model(), rows))
    assert sources["int8"](rows).shape == (len(rows),)


def test_every_model_an_export_lists_is_read(tmp_path):
    exported = _export(tmp_path, _model(), _rows(),
                       meta={"run": "results/20260101-000000",
                             "models": [{"k": 4, "h": 8}, {"k": 6, "h": 32}]})
    assert models_in(str(tmp_path / "quantize" / exported))[1] == [(4, 8), (6, 32)]


def test_an_export_naming_one_pair_on_its_own_is_still_read(tmp_path):
    exported = _export(tmp_path, _model(), _rows(),
                       meta={"run": "results/20260101-000000", "k": 4, "h": 8})
    assert models_in(str(tmp_path / "quantize" / exported))[1] == [(4, 8)]


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
    write([("ae", model)], rows, str(tmp_path / "out"), batch=128)
    got = onnx_residuals(str(tmp_path / "out" / "ae_float.onnx"), rows[:8])
    assert np.allclose(got, residuals(rows[:8], model), atol=1e-6)
