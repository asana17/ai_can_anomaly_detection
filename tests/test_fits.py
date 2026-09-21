import numpy as np
import pytest

from models.fits import (FitArguments, LinearAe, NonlinearAe, Pca, as_dict,
                         model_from, models_from)

ROWS = np.random.default_rng(0).normal(size=(64, 5)).astype(np.float32)
ARGUMENTS = FitArguments(epochs=2, batch=16, rate=1e-3, improvement=1e-4, patience=2,
                         seed=0)


def test_a_listed_value_stands_for_one_model_per_value():
    listed = [{"model": "pca", "k": [2, 4]},
              {"model": "nonlinear ae", "k": [2], "hidden": [32, 64],
               "epochs": 2, "batch": 16, "rate": 1e-3, "improvement": 1e-4,
               "patience": 2, "seed": 0}]
    assert models_from(listed) == [Pca(2), Pca(4), NonlinearAe(2, 32, ARGUMENTS),
                                   NonlinearAe(2, 64, ARGUMENTS)]


def test_a_model_is_named_as_the_tables_name_it():
    assert Pca(2).name == "rules + pca k=2"
    assert NonlinearAe(8, 128, ARGUMENTS).name == "rules + nonlinear ae h=128 k=8"


def test_the_tensors_keep_the_names_quantize_reads():
    assert Pca(2).prefix == "pca.k2."
    assert LinearAe(2, ARGUMENTS).prefix == "linear_ae.k2."
    assert NonlinearAe(8, 128, ARGUMENTS).prefix == "nonlinear_ae.h128.k8."


@pytest.mark.parametrize("model", [Pca(2), LinearAe(2, ARGUMENTS),
                                   NonlinearAe(2, 8, ARGUMENTS)])
def test_a_written_model_reads_back_the_same(model):
    assert model_from(as_dict(model)) == model


def test_only_an_autoencoder_writes_down_how_it_was_fitted():
    assert as_dict(Pca(2)) == {"model": "pca", "k": 2}
    assert as_dict(LinearAe(2, ARGUMENTS))["rate"] == 1e-3


@pytest.mark.parametrize("model", [Pca(2), LinearAe(2, ARGUMENTS),
                                   NonlinearAe(2, 8, ARGUMENTS)])
def test_a_loaded_model_scores_as_the_fitted_one_did(model):
    tensors, score, _ = model.fit(ROWS)
    assert np.allclose(model.scorer(tensors, ROWS.shape[1])(ROWS), score(ROWS))


def test_loading_a_model_the_weights_lack_raises():
    with pytest.raises(ValueError):
        Pca(2).scorer({}, 5)


def test_only_an_autoencoder_reports_a_loss_for_each_epoch():
    assert Pca(2).fit(ROWS)[2] is None
    assert len(LinearAe(2, ARGUMENTS).fit(ROWS)[2]) == 2
