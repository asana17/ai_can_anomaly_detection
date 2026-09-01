from math import sqrt

from preprocess.features.normalize import fit, normalize


def test_fit_computes_mean_and_std():
    stats = fit([[0.0, 10.0], [2.0, 10.0], [4.0, 10.0]])
    assert stats[0][0] == 2.0
    assert round(stats[0][1], 6) == round(sqrt(8 / 3), 6)
    assert stats[1] == (10.0, 0.0)  # constant column


def test_normalize_z_scores():
    stats = [(2.0, 2.0)]
    assert normalize([4.0], stats) == [1.0]
    assert normalize([0.0], stats) == [-1.0]


def test_constant_signal_maps_to_zero():
    assert normalize([10.0], [(10.0, 0.0)]) == [0.0]


def test_value_beyond_training_range_is_not_clipped():
    # wheel speed mean 40, std 20; a value of 100 is unusual, not clipped
    assert normalize([100.0], [(40.0, 20.0)]) == [3.0]
