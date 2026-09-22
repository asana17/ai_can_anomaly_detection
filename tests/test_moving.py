import numpy as np

from preprocess.features.moving import moving, moving_spans
from preprocess.features.signal_state import SIGNALS


def test_moving_is_the_rows_over_the_speed_given():
    raw = np.zeros((5, len(SIGNALS)), np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = [0.0, 4.9, 5.0, 5.1, 80.0]
    assert moving(raw, min_speed=5.0).tolist() == [False, False, False, True, True]


def test_moving_spans_split_at_stops_and_missing_rows():
    speeds = {0.0: 10.0, 0.1: 10.0, 0.2: 0.0, 0.3: 10.0, 0.6: 10.0, 0.7: float("nan")}
    rows = {}
    for t, kmh in speeds.items():
        rows[t] = np.zeros(len(SIGNALS), np.float32)
        rows[t][SIGNALS.index("wheel_speed")] = kmh
    assert moving_spans(rows, min_speed=5.0, period=0.1) == [
        (0.0, 0.1), (0.3, 0.3), (0.6, 0.6)]
