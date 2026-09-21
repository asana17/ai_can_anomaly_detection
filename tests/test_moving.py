import numpy as np

from preprocess.features.moving import moving
from preprocess.features.signal_state import SIGNALS


def test_moving_is_the_rows_over_the_speed_given():
    raw = np.zeros((5, len(SIGNALS)), np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = [0.0, 4.9, 5.0, 5.1, 80.0]
    assert moving(raw, min_speed=5.0).tolist() == [False, False, False, True, True]
