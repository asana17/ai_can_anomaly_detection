import numpy as np
import pytest
import torch

from models import autoencoder
from common.schema_validate import check
from models.fits import (FitArguments, LinearAe, NonlinearAe, Pca, Var, WindowDeltaAe,
                         WindowNonlinearAe, as_dict, model_from, models_from)

ROWS = np.random.default_rng(0).normal(size=(64, 5)).astype(np.float32)
WINDOWS = np.random.default_rng(1).normal(size=(64, 3, 5)).astype(np.float32)
ARGUMENTS = FitArguments(epochs=2, batch=16, rate=1e-3, improvement=1e-4, patience=2,
                         seed=0)


def test_a_listed_value_stands_for_one_model_per_value():
    listed = [{"model": "pca", "k": [2, 4]}, {"model": "var", "rows": [5, 10]},
              {"model": "nonlinear ae", "k": [2], "hidden": [32, 64],
               "epochs": 2, "batch": 16, "rate": 1e-3, "improvement": 1e-4,
               "patience": 2, "seed": 0}]
    assert models_from(listed) == [Pca(2), Pca(4), Var(5), Var(10), NonlinearAe(2, 32, ARGUMENTS),
                                   NonlinearAe(2, 64, ARGUMENTS)]


def test_a_model_is_named_by_its_values():
    assert Pca(2).name == "pca k=2"
    assert Var(10).name == "var r=10"
    assert NonlinearAe(8, 128, ARGUMENTS).name == "nonlinear ae h=128 k=8"
    assert WindowNonlinearAe(10, 8, 128, ARGUMENTS).name == "window nonlinear ae r=10 h=128 k=8"


def test_the_tensors_keep_the_names_quantize_reads():
    assert Pca(2).prefix == "pca.k2."
    assert Var(10).prefix == "var.r10."
    assert LinearAe(2, ARGUMENTS).prefix == "linear_ae.k2."
    assert NonlinearAe(8, 128, ARGUMENTS).prefix == "nonlinear_ae.h128.k8."
    assert WindowNonlinearAe(10, 8, 128, ARGUMENTS).prefix == "window_nonlinear_ae.r10.h128.k8."


@pytest.mark.parametrize("model", [Pca(2), Var(5), LinearAe(2, ARGUMENTS),
                                   NonlinearAe(2, 8, ARGUMENTS),
                                   WindowNonlinearAe(3, 2, 8, ARGUMENTS)])
def test_a_written_model_reads_back_the_same(model):
    assert model_from(as_dict(model)) == model


def test_only_an_autoencoder_writes_down_how_it_was_fitted():
    assert as_dict(Pca(2)) == {"model": "pca", "k": 2}
    assert as_dict(Var(5)) == {"model": "var", "rows": 5}
    assert as_dict(LinearAe(2, ARGUMENTS))["rate"] == 1e-3


@pytest.mark.parametrize("model", [Pca(2), LinearAe(2, ARGUMENTS),
                                   NonlinearAe(2, 8, ARGUMENTS)])
def test_a_loaded_model_scores_as_the_fitted_one_did(model):
    tensors, score, _ = model.fit(ROWS)
    assert np.allclose(model.scorer(tensors, ROWS.shape[1])(ROWS), score(ROWS))


def test_a_loaded_var_scores_windows_as_the_fitted_one_did():
    tensors, score, _ = Var(3).fit(WINDOWS)
    assert np.allclose(Var(3).scorer(tensors, WINDOWS.shape[2])(WINDOWS),
                       score(WINDOWS))


def test_a_loaded_window_nonlinear_ae_scores_windows_as_the_fitted_one_did():
    model = WindowNonlinearAe(3, 2, 8, ARGUMENTS)
    tensors, score, _ = model.fit(WINDOWS)
    assert np.allclose(model.scorer(tensors, WINDOWS.shape[2])(WINDOWS),
                       score(WINDOWS))


def test_a_window_goes_into_the_window_nonlinear_ae_flat_and_oldest_row_first():
    model = WindowNonlinearAe(3, 2, 8, ARGUMENTS)
    tensors, score, _ = model.fit(WINDOWS)

    net = model.network_with_weights(tensors, WINDOWS.shape[2])
    flat = np.concatenate([WINDOWS[:, 0], WINDOWS[:, 1], WINDOWS[:, 2]], axis=1)
    assert np.allclose(autoencoder.residuals(flat, net, WINDOWS.shape[2]),
                       score(WINDOWS))


def test_a_window_nonlinear_ae_listed_with_the_var_spreads_into_one_model_per_value():
    listed = [{"model": "var", "rows": [5]},
              {"model": "window nonlinear ae", "rows": [5, 10], "k": [2], "hidden": [32],
               "epochs": 2, "batch": 16, "rate": 1e-3, "improvement": 1e-4,
               "patience": 2, "seed": 0}]
    assert models_from(listed) == [Var(5), WindowNonlinearAe(5, 2, 32, ARGUMENTS),
                                   WindowNonlinearAe(10, 2, 32, ARGUMENTS)]


def test_a_window_nonlinear_ae_written_down_meets_the_models_schema():
    check([as_dict(Var(5)), as_dict(WindowNonlinearAe(5, 2, 32, ARGUMENTS))], "models.schema.json")


def test_models_written_before_the_window_nonlinear_ae_still_read():
    var_only = [{"model": "var", "rows": 5}, {"model": "var", "rows": 10}]
    instant = [{"model": "nonlinear ae", "k": 8, "hidden": 128, "epochs": 2,
                "batch": 16, "rate": 1e-3, "improvement": 1e-4, "patience": 2,
                "seed": 0}]
    check(var_only, "models.schema.json")
    check(instant, "models.schema.json")
    assert models_from(var_only) == [Var(5), Var(10)]
    assert models_from(instant) == [NonlinearAe(8, 128, ARGUMENTS)]


def test_loading_a_model_the_weights_lack_raises():
    with pytest.raises(ValueError):
        Pca(2).scorer({}, 5)


def test_only_an_autoencoder_reports_a_loss_for_each_epoch():
    assert Pca(2).fit(ROWS)[2] is None
    assert Var(3).fit(WINDOWS)[2] is None
    assert len(LinearAe(2, ARGUMENTS).fit(ROWS)[2]) == 2


def test_a_network_comes_back_with_the_tensors_the_run_saved():
    model = NonlinearAe(2, 8, ARGUMENTS)
    tensors, _, _ = model.fit(ROWS)

    net = model.network_with_weights(tensors, ROWS.shape[1])
    assert all(np.allclose(net.state_dict()[name].numpy(),
                           tensors[f"{model.prefix}{name}"].numpy())
               for name in net.state_dict())


def test_a_window_delta_ae_is_named_apart_from_the_window_nonlinear_ae():
    model = WindowDeltaAe(10, 8, 128, ARGUMENTS, stride=3)
    assert model.name == "window delta ae r=10 s=3 h=128 k=8"
    assert model.prefix == "window_delta_ae.r10.s3.h128.k8."
    assert model_from(as_dict(model)) == model


def test_a_window_delta_ae_scores_the_error_on_its_last_scaled_step():
    model = WindowDeltaAe(3, 2, 8, ARGUMENTS)
    tensors, score, _ = model.fit(WINDOWS)
    std = np.diff(WINDOWS, axis=1).std(axis=(0, 1))
    assert np.allclose(tensors[f"{model.prefix}step_std"].numpy(), std)

    net = model.network_with_weights(tensors, WINDOWS.shape[2])
    step = (np.diff(WINDOWS, axis=1) / std).reshape(len(WINDOWS), -1).astype(np.float32)
    rebuilt = net.steps(torch.from_numpy(step)).detach().numpy()
    last = WINDOWS.shape[2]
    assert np.allclose(((rebuilt - step)[:, -last:] ** 2).mean(axis=1), score(WINDOWS),
                       atol=1e-6)
    assert np.allclose(model.scorer(tensors, WINDOWS.shape[2])(WINDOWS), score(WINDOWS))


def test_a_window_delta_ae_written_down_meets_the_models_schema():
    check([as_dict(WindowDeltaAe(5, 2, 32, ARGUMENTS, stride=3))], "models.schema.json")
