"""Flag the engine and wheel speeds not matching the gear the transmission reports.

Each gear turns the engine a set number of times per km/h. The gears are spaced 1.28
apart, so a measured ratio picks out one of them, and it should be the reported one.
No tolerance is needed for that, only the table.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS

# The median of engine_speed / wheel_speed in each gear, over 150,291 evaluations
# with the clutch closed. Gears 1 and 3 are too rare in the data to place.
RATIOS = {2: 179.25, 4: 108.69, 5: 87.02, 6: 67.20, 7: 52.27,
          8: 41.37, 9: 31.69, 10: 24.82, 11: 19.37, 12: 15.24}

def nearest_gear(ratio: np.ndarray, ratios: dict = RATIOS) -> np.ndarray:
    """The gear whose ratio is closest to each of `ratio`, compared as a proportion."""
    ratio = np.asarray(ratio)
    ratio = ratio.astype(np.result_type(ratio, np.float32))[..., None]
    gears = np.array(list(ratios))
    table = np.array(list(ratios.values()), dtype=ratio.dtype)
    return gears[np.maximum(table / ratio, ratio / table).argmin(axis=-1)]


def hits(raw: np.ndarray, min_speed: float, ratios: dict = RATIOS) -> np.ndarray:
    """True where the speeds pick out a gear other than the reported one.

    Below `min_speed` the wheel speed is too coarse for the ratio, as in shaft_ratio.
    """
    engine = raw[:, SIGNALS.index("engine_speed")]
    wheel = raw[:, SIGNALS.index("wheel_speed")]
    gear = raw[:, SIGNALS.index("current_gear")]
    selected = raw[:, SIGNALS.index("selected_gear")]
    slip = raw[:, SIGNALS.index("clutch_slip")]
    # mid shift or with the clutch open there is no fixed ratio
    fixed = ((wheel >= min_speed) & np.isin(gear, list(ratios)) & (gear == selected)
             & (slip == 0))
    turning = fixed & (engine > 0)
    ratio = np.divide(engine, wheel, out=np.ones_like(wheel), where=turning)
    # the closed clutch turns the engine with the wheels, so a stopped engine
    # contradicts the speed above
    return (fixed & (engine <= 0)) | (turning & (nearest_gear(ratio, ratios) != gear))
