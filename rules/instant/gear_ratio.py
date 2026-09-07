"""Flag the engine and wheel speeds not matching the gear the transmission reports.

Each gear turns the engine a set number of times per km/h. The gears are spaced 1.28
apart, so a measured ratio picks out one of them, and it should be the reported one.
No tolerance is needed for that, only the table.
"""

from __future__ import annotations

# The median of engine_speed / wheel_speed in each gear, over 150,291 evaluations
# with the clutch closed. Gears 1 and 3 are too rare in the data to place.
RATIOS = {2: 179.25, 4: 108.69, 5: 87.02, 6: 67.20, 7: 52.27,
          8: 41.37, 9: 31.69, 10: 24.82, 11: 19.37, 12: 15.24}

# Below this the wheel speed is too coarse for the ratio, as in shaft_ratio.
MIN_SPEED = 5.0

NAMES = ["engine_speed", "wheel_speed", "current_gear"]


def nearest_gear(ratio: float, ratios: dict = RATIOS) -> int:
    """The gear whose ratio is closest to `ratio`, compared as a proportion."""
    return min(ratios, key=lambda gear: max(ratios[gear] / ratio, ratio / ratios[gear]))


def violations(values: dict, ratios: dict = RATIOS, min_speed: float = MIN_SPEED) -> list:
    """The three names, if the speeds pick out a gear other than the reported one."""
    engine, wheel = values.get("engine_speed"), values.get("wheel_speed")
    gear, selected = values.get("current_gear"), values.get("selected_gear")
    slip = values.get("clutch_slip")
    if None in (engine, wheel, gear, selected, slip) or wheel < min_speed:
        return []
    if gear not in ratios or gear != selected or slip != 0:
        return []          # mid shift or with the clutch open there is no fixed ratio
    return [] if nearest_gear(engine / wheel, ratios) == gear else NAMES
