import numpy as np

from models.var import autoregression, residuals


def _windows(seed=0, signals=4, rows=5, n=3000, noise=0.0, offset=0.0):
    """Windows where each row follows from the one before, `noise` on the last row."""
    rng = np.random.default_rng(seed)
    step = 0.9 * np.linalg.qr(rng.normal(size=(signals, signals)))[0]
    series = [rng.normal(size=(n, signals))]
    for _ in range(rows - 1):
        series.append(series[-1] @ step)
    windows = np.stack(series, axis=1) + offset
    windows[:, -1] += rng.normal(scale=noise, size=(n, signals))
    return windows


def test_the_coefficients_take_every_row_before_the_last():
    fitted = autoregression(_windows(signals=4, rows=5))
    assert fitted.coefficients.shape == (4, 4 * 4)
    assert fitted.intercept.shape == (4,)


def test_a_window_that_follows_the_fit_leaves_nothing_behind():
    windows = _windows(offset=100.0)      # far from the origin, so the intercept counts
    assert residuals(windows, autoregression(windows)).max() < 1e-6


def test_a_pushed_last_row_stands_out():
    windows = _windows(noise=0.01)
    fitted = autoregression(windows)
    moved = windows.copy()
    moved[0, -1] += 5.0
    assert residuals(moved, fitted)[0] > 50 * np.percentile(residuals(windows, fitted),
                                                            99)


def test_the_rows_are_read_oldest_first():
    windows = _windows(noise=0.01)
    fitted = autoregression(windows)
    normal = np.percentile(residuals(windows, fitted), 99)
    assert np.median(residuals(windows[:, ::-1], fitted)) > 50 * normal
