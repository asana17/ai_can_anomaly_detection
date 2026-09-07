import numpy as np

from models.pca import explained, fit, residuals


def _rows(seed=0, latent=3, signals=17, n=2000, noise=0.01):
    """Rows that really vary in `latent` directions, dressed up as `signals` columns."""
    rng = np.random.default_rng(seed)
    return (rng.normal(size=(n, latent)) @ rng.normal(size=(latent, signals))
            + rng.normal(scale=noise, size=(n, signals)))


def test_explained_finds_the_real_number_of_directions():
    share = explained(_rows(latent=3))
    assert share[:3].sum() > 0.999
    assert share[3] < 0.001


def test_a_basis_has_one_column_per_component():
    assert fit(_rows(), 4).shape == (17, 4)


def test_keeping_every_direction_leaves_nothing_behind():
    rows = _rows(latent=3, noise=0.0)
    assert residuals(rows, fit(rows, 3)).max() < 1e-6


def test_a_row_pushed_off_the_subspace_stands_out():
    rows = _rows(latent=3)
    basis = fit(rows, 3)
    normal = residuals(rows, basis)
    moved = rows.copy()
    moved[0] += 5.0
    assert residuals(moved, basis)[0] > 50 * np.percentile(normal, 99)


def test_a_row_moved_along_the_subspace_does_not():
    rows = _rows(latent=3)
    basis = fit(rows, 3)
    moved = rows.copy()
    moved[0] += 5.0 * basis[:, 0]           # further out, but in a direction rows vary in
    assert residuals(moved, basis)[0] < 10 * np.percentile(residuals(rows, basis), 99)


def test_more_components_never_leave_more_behind():
    rows = _rows()
    last = np.inf
    for k in (1, 2, 4, 8, 16):
        now = residuals(rows, fit(rows, k)).mean()
        assert now <= last + 1e-9
        last = now
