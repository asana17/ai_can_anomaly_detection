from rules.gear_ratio import NAMES, RATIOS, nearest_gear, violations


def _values(**over):
    v = {"engine_speed": RATIOS[12] * 80, "wheel_speed": 80.0, "current_gear": 12,
         "selected_gear": 12, "clutch_slip": 0.0}
    v.update(over)
    return v


def test_every_table_ratio_picks_its_own_gear():
    for gear, ratio in RATIOS.items():
        assert nearest_gear(ratio) == gear


def test_the_reported_gear_matching_the_speeds_passes():
    assert violations(_values()) == []


def test_a_gear_two_steps_from_the_speeds_is_flagged():
    assert violations(_values(current_gear=10, selected_gear=10)) == NAMES


def test_the_measured_spread_inside_a_gear_still_passes():
    # top gear sits within 1.7% of its median, well inside the 12.8% to its neighbour
    assert violations(_values(engine_speed=RATIOS[12] * 80 * 1.017)) == []


def test_a_reading_past_the_midpoint_takes_the_neighbour():
    midpoint = (RATIOS[12] * RATIOS[11]) ** 0.5
    assert violations(_values(engine_speed=midpoint * 80 * 1.01)) == NAMES


def test_it_stays_quiet_while_shifting():
    assert violations(_values(current_gear=10)) == []


def test_it_stays_quiet_with_the_clutch_open():
    assert violations(_values(current_gear=10, selected_gear=10, clutch_slip=50.0)) == []


def test_it_stays_quiet_below_the_speed_gate():
    assert violations(_values(wheel_speed=4.0, current_gear=10, selected_gear=10)) == []


def test_it_stays_quiet_for_a_gear_the_table_does_not_hold():
    assert violations(_values(current_gear=1, selected_gear=1)) == []


def test_it_says_nothing_until_every_signal_has_arrived():
    v = _values()
    for name in v:
        assert violations({k: x for k, x in v.items() if k != name}) == []
