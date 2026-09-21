import ctypes

import numpy as np
import pytest

from common.settings import Settings
from preprocess.features.signal_state import SIGNALS
from rules.hits import instant, rule_hits
from rules.instant.gear_ratio import RATIOS

ROWS = 100_000
BREAKERS = 10
UNTOUCHED = 15  # draws that leave a row consistent, beside one per breaker


@pytest.fixture(scope="module")
def c_rule_hits(board_lib):
    """Build board/lib/rules for this machine and give its `rule_hits`."""
    function = board_lib(["rules"],
                         '#include "rule_hits.h"\n'
                         "bool hits(const float *row, float min_speed)\n"
                         "{\n\treturn rule_hits(row, min_speed);\n}\n").hits
    function.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_float]
    function.restype = ctypes.c_bool
    return function


def _consistent(rng):
    """Rows no rule hits: one gear's ratio, both speeds and the shaft agreeing."""
    raw = np.zeros((ROWS, len(SIGNALS)))
    column = {name: i for i, name in enumerate(SIGNALS)}
    gears = rng.choice(list(RATIOS), ROWS)
    engine = rng.uniform(600.0, 2200.0, ROWS)
    wheel = engine / np.array([RATIOS[gear] for gear in gears])
    steering = rng.uniform(-0.5, 0.5, ROWS)
    raw[:, column["engine_speed"]] = engine
    raw[:, column["wheel_speed"]] = wheel
    raw[:, column["tachograph_speed"]] = wheel + rng.uniform(-1.5, 1.5, ROWS)
    raw[:, column["output_shaft_speed"]] = wheel * rng.uniform(13.2, 17.3, ROWS)
    raw[:, column["input_shaft_speed"]] = engine
    raw[:, column["selected_gear"]] = gears
    raw[:, column["current_gear"]] = gears
    raw[:, column["accel_pedal"]] = rng.uniform(2.0, 100.0, ROWS)
    raw[:, column["engine_load"]] = rng.uniform(0.0, 100.0, ROWS)
    raw[:, column["driver_demand_torque"]] = rng.uniform(-100.0, 100.0, ROWS)
    raw[:, column["actual_engine_torque"]] = rng.uniform(-100.0, 100.0, ROWS)
    raw[:, column["fuel_rate"]] = rng.uniform(0.0, 100.0, ROWS)
    raw[:, column["steering_angle"]] = steering
    raw[:, column["yaw_rate"]] = np.sign(steering) * rng.uniform(0.1, 0.5, ROWS)
    raw[:, column["lateral_accel"]] = rng.uniform(-5.0, 5.0, ROWS)
    return raw, column


def _next_gear(gears):
    """The gear after each of `gears` in the table, so the ratio picks out another one."""
    table = np.array(list(RATIOS))
    return table[(np.searchsorted(table, gears) + 1) % len(table)]


def _break(raw, column, rng, rows, breaker):
    """Move one signal of `rows` until a rule hits them."""
    drawn = rng.uniform(size=len(rows))
    if breaker == 0:
        raw[rows, column["tachograph_speed"]] += 2.0 + 5.0 * drawn
    elif breaker == 1:
        raw[rows, column["output_shaft_speed"]] = (raw[rows, column["wheel_speed"]]
                                                   * (5.0 + 25.0 * drawn))
    elif breaker == 2:
        raw[rows, column["current_gear"]] = _next_gear(raw[rows, column["current_gear"]])
        raw[rows, column["selected_gear"]] = raw[rows, column["current_gear"]]
    elif breaker == 3:
        raw[rows, column["yaw_rate"]] *= -1.0
    elif breaker == 4:
        raw[rows, column["engine_speed"]] = 0.0
        # gear 1 is not in the ratio table, so gear_ratio stays quiet on the stopped engine
        raw[rows, column["current_gear"]] = 1.0
        raw[rows, column["selected_gear"]] = 1.0
    elif breaker == 5:
        raw[rows, column["brake_pedal"]] = 1.0 + 99.0 * drawn
    elif breaker == 6:
        raw[rows, column["current_gear"]] = -1.0
        raw[rows, column["wheel_speed"]] += 10.0
        raw[rows, column["tachograph_speed"]] = raw[rows, column["wheel_speed"]]
        raw[rows, column["output_shaft_speed"]] = raw[rows, column["wheel_speed"]] * 15.0
    elif breaker == 7:
        raw[rows, column["wheel_speed"]] = 0.0
        raw[rows, column["tachograph_speed"]] = 0.0
        raw[rows, column["output_shaft_speed"]] = 51.0 + drawn
    elif breaker == 8:
        raw[rows, rows % len(SIGNALS)] = 1e6
    elif breaker == 9:
        raw[rows, rows % len(SIGNALS)] = np.nan


def _rows(rng):
    """Consistent rows, two in five of them with one signal moved to hit a rule."""
    raw, column = _consistent(rng)
    drawn = rng.integers(-UNTOUCHED, BREAKERS, ROWS)
    for breaker in range(BREAKERS):
        _break(raw, column, rng, np.flatnonzero(drawn == breaker), breaker)
    return np.ascontiguousarray(raw.astype(np.float32))


def test_the_c_port_matches_the_python(c_rule_hits):
    """The C port ORs the instant rules as `rule_hits` does.

    Every rule hits rows no other rule hits, so one left out of the OR shows here.
    """
    settings = Settings()
    raw = _rows(np.random.default_rng(0))
    expected = rule_hits(raw, settings)
    row = ctypes.POINTER(ctypes.c_float)
    got = np.array([c_rule_hits(raw[i].ctypes.data_as(row), settings.MIN_SPEED)
                    for i in range(ROWS)])
    alone = np.sum([check(raw) for check in instant(settings)], axis=0) == 1
    assert all((alone & check(raw)).any() for check in instant(settings))
    assert expected.any() and not expected.all()
    assert np.flatnonzero(got != expected).tolist() == []
