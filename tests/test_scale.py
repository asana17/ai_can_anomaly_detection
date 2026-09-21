import numpy as np

from assemble.scale import scale_for
from preprocess.features.scale import Scale


def test_scale_for_standardizes_the_rows_it_was_given():
    rows = np.array([[600.0, 10.0], [800.0, 20.0], [1000.0, 30.0], [2000.0, 40.0]],
                    np.float32)
    scaled = scale_for(rows).apply(rows)

    assert np.allclose(scaled.mean(axis=0), 0.0, atol=1e-4)
    assert np.allclose(scaled.std(axis=0), 1.0, atol=1e-4)


def test_undo_takes_back_what_apply_put_on():
    scale = Scale(np.array([1300.0, 25.0], np.float32), np.array([500.0, 10.0], np.float32))
    rows = np.array([[900.0, 5.0], [900.0, 80.0]], np.float32)

    assert np.allclose(scale.undo(scale.apply(rows)), rows, atol=1e-3)
