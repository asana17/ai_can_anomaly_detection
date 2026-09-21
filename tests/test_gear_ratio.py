import numpy as np

from preprocess.features.signal_state import SIGNALS
from rules.instant.gear_ratio import RATIOS, hits, nearest_gear


def _hit(values, **kwargs):
    """Whether the rule hits one row carrying `values`, every other signal at 0."""
    raw = np.zeros((1, len(SIGNALS)))
    for name, value in values.items():
        raw[0, SIGNALS.index(name)] = value
    return bool(hits(raw, **kwargs)[0])


GATE = 5.0


def _values(**over):
    v = {"engine_speed": RATIOS[12] * 80, "wheel_speed": 80.0, "current_gear": 12,
         "selected_gear": 12, "clutch_slip": 0.0}
    v.update(over)
    return v


def test_every_table_ratio_picks_its_own_gear():
    for gear, ratio in RATIOS.items():
        assert nearest_gear(ratio) == gear


def test_the_reported_gear_matching_the_speeds_passes():
    assert not _hit(_values(), min_speed=GATE)


def test_a_gear_two_steps_from_the_speeds_is_flagged():
    assert _hit(_values(current_gear=10, selected_gear=10), min_speed=GATE)


def test_the_measured_spread_inside_a_gear_still_passes():
    # top gear sits within 1.7% of its median, well inside the 12.8% to its neighbour
    assert not _hit(_values(engine_speed=RATIOS[12] * 80 * 1.017), min_speed=GATE)


def test_a_reading_past_the_midpoint_takes_the_neighbour():
    midpoint = (RATIOS[12] * RATIOS[11]) ** 0.5
    assert _hit(_values(engine_speed=midpoint * 80 * 1.01), min_speed=GATE)


def test_it_stays_quiet_while_shifting():
    assert not _hit(_values(current_gear=10), min_speed=GATE)


def test_it_stays_quiet_with_the_clutch_open():
    values = _values(current_gear=10, selected_gear=10, clutch_slip=50.0)
    assert not _hit(values, min_speed=GATE)


def test_it_stays_quiet_below_the_speed_gate():
    values = _values(wheel_speed=GATE - 1.0, current_gear=10, selected_gear=10)
    assert not _hit(values, min_speed=GATE)


def test_it_stays_quiet_for_a_gear_the_table_does_not_hold():
    assert not _hit(_values(current_gear=1, selected_gear=1), min_speed=GATE)


def test_a_stopped_engine_cannot_be_in_gear_and_moving():
    assert _hit(_values(engine_speed=0.0, wheel_speed=60.0), min_speed=GATE)
