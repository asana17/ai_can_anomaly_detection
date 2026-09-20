import numpy as np

from assemble.grid import grid_rows, moving
from assemble.scale import scale_for
from assemble.train_set import apart_from_test, split_rows
from preprocess.features.signal_state import SIGNALS

PERIOD, MAX_HOLD = 0.1, 1.0


def _ts(t):
    whole = int(t)
    frac = round((t - whole) * 1_000_000)
    return f"2020-11-23 08:00:{whole:02d}.{frac:06d}"


def _write_log(path, rpms, period=0.1, gap_after=None, gap=0.0):
    """Write a log, jumping `gap` seconds after `gap_after` samples if given."""
    lines = ["timestamp;id;dlc;data"]
    t = 0.0
    for i, rpm in enumerate(rpms):
        ts = _ts(t)
        raw = round(rpm / 0.125)
        lines.append(f"{ts};0x18F004E6;8;0;0;0;{raw & 0xFF};{(raw >> 8) & 0xFF};0;0;0")  # EEC1
        lines.append(f"{ts};0x18F003E6;8;0;0;0;0;0;0;0;0")  # EEC2
        lines.append(f"{ts};0x18FEF1E6;8;0;0;0;0;0;0;0;0")  # CCVS1
        lines.append(f"{ts};0x18FEF2E6;8;10;0;255;255;255;255;255;255")  # LFE1
        lines.append(f"{ts};0x18F009E6;8;127;125;96;127;125;135;127;255")  # VDC2
        lines.append(f"{ts};0x18F001E6;8;207;0;207;255;255;255;255;255")  # EBC1
        lines.append(f"{ts};0x18FE6CE6;8;0;0;192;192;0;0;0;0")  # TCO1
        lines.append(f"{ts};0x18F002E6;8;205;32;28;0;252;32;28;255")  # ETC1
        lines.append(f"{ts};0x18F005E6;8;137;0;0;137;0;0;0;0")  # ETC2
        t += period + (gap if gap_after is not None and i + 1 == gap_after else 0.0)
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def test_grid_rows_returns_2d_signal_rows(tmp_path):
    rows, times, segments = grid_rows([_write_log(tmp_path / "a.csv", [800] * 6)], period=PERIOD, max_hold=MAX_HOLD)
    assert rows.ndim == 2 and rows.shape[1] == 17
    assert times.shape == segments.shape == (len(rows),)


def test_grid_rows_keeps_the_time_of_each_row(tmp_path):
    _, times, _ = grid_rows([_write_log(tmp_path / "a.csv", [800] * 6)], period=PERIOD, max_hold=MAX_HOLD)
    assert times.dtype == np.float64          # epoch seconds lose 0.1 s in float32
    assert np.allclose(np.diff(times), 0.1)


def test_segments_break_between_files(tmp_path):
    files = [_write_log(tmp_path / "a.csv", [800] * 6),
             _write_log(tmp_path / "b.csv", [900] * 6)]
    _, _, segments = grid_rows(files, period=PERIOD, max_hold=MAX_HOLD)
    assert len(set(segments)) == 2
    assert segments[0] != segments[-1]


def test_segments_break_across_a_gap(tmp_path):
    # one file, but the log jumps 30 s after the 4th sample
    log = _write_log(tmp_path / "a.csv", [800] * 10, gap_after=4, gap=30.0)
    _, times, segments = grid_rows([log], period=PERIOD, max_hold=MAX_HOLD)
    assert len(set(segments)) == 2, "the gap must start a new segment"
    first, second = (times[segments == s] for s in sorted(set(segments)))
    assert second[0] - first[-1] > 1.0                  # the gap is not bridged
    for run in (first, second):
        assert np.allclose(np.diff(run), 0.1)           # each segment is evenly spaced


def test_scale_for_standardizes_the_rows_it_was_given(tmp_path):
    log = _write_log(tmp_path / "tr.csv", [600, 800, 1000, 1200, 1400, 1600, 1800, 2000])
    rows, _, _ = grid_rows([log], period=PERIOD, max_hold=MAX_HOLD)
    scaled = scale_for(rows).apply(rows)

    engine_speed = scaled[:, 0]               # first signal in SIGNALS order
    assert abs(engine_speed.mean()) < 1e-4
    assert abs(engine_speed.std() - 1.0) < 1e-4


def test_the_scale_it_fits_puts_other_rows_on_the_same_scale(tmp_path):
    train = _write_log(tmp_path / "tr.csv", [600, 800, 1000, 1200, 1400, 1600, 1800, 2000])
    other = _write_log(tmp_path / "te.csv", [900] * 6)
    scale = scale_for(grid_rows([train], period=PERIOD, max_hold=MAX_HOLD)[0])
    rows, _, _ = grid_rows([other], period=PERIOD, max_hold=MAX_HOLD)

    assert np.allclose(scale.undo(scale.apply(rows)), rows, atol=1e-3)


def _rows(speeds):
    """Rows carrying only a wheel speed, one per 100 ms, with their times."""
    raw = np.zeros((len(speeds), 17), np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = speeds
    return raw, np.arange(len(speeds), dtype=np.float64) * 0.1


def test_moving_is_the_rows_over_the_speed_given():
    raw, _ = _rows([0.0, 4.9, 5.0, 5.1, 80.0])
    assert moving(raw, min_speed=5.0).tolist() == [False, False, False, True, True]


def test_split_rows_gives_calibration_the_share_of_the_seconds_asked_for():
    raw, t = _rows(np.full(100000, 50.0))
    train_rows, calibration_rows = split_rows(raw, t, share=0.10, block=20.0, gap=0.0,
                                     min_speed=5.0, period=PERIOD)
    assert abs(calibration_rows.mean() - 0.10) < 0.01


def test_split_rows_cuts_calibration_into_windows_of_the_block_length():
    raw, t = _rows(np.full(10000, 50.0))
    _, calibration_rows = split_rows(raw, t, share=0.10, block=20.0, gap=0.0,
                                     min_speed=5.0, period=PERIOD)
    edges = np.flatnonzero(np.diff(np.concatenate(
        [[0], calibration_rows.astype(np.int8), [0]])))
    assert set((edges[1::2] - edges[::2]).tolist()) == {200}   # 20 s at 100 ms


def test_split_rows_spreads_the_windows_over_the_period():
    raw, t = _rows(np.full(100000, 50.0))
    _, calibration_rows = split_rows(raw, t, share=0.10, block=20.0, gap=0.0,
                                     min_speed=5.0, period=PERIOD)
    at = np.flatnonzero(calibration_rows)
    assert at[0] < 1000 and at[-1] > 90000


def test_split_rows_never_calibrates_on_a_stopped_row():
    speeds = np.full(20000, 50.0)
    speeds[1::2] = 0.0                          # the truck stops every other row
    raw, t = _rows(speeds)
    _, calibration_rows = split_rows(raw, t, share=0.10, block=20.0, gap=0.0,
                                     min_speed=5.0, period=PERIOD)
    assert calibration_rows.any() and not (calibration_rows & (speeds == 0.0)).any()


def test_split_rows_measures_the_block_in_seconds_above_min_speed():
    speeds = np.full(20000, 50.0)
    speeds[1::2] = 0.0
    raw, t = _rows(speeds)
    _, calibration_rows = split_rows(raw, t, share=0.10, block=20.0, gap=0.0,
                                     min_speed=5.0, period=PERIOD)
    assert abs(calibration_rows.sum() / (speeds > 5.0).sum() - 0.10) < 0.01


def test_split_rows_puts_no_row_in_both_parts():
    raw, t = _rows(np.full(10000, 50.0))
    train_rows, calibration_rows = split_rows(raw, t, share=0.10, block=20.0, gap=5.0,
                                     min_speed=5.0, period=PERIOD)
    assert not (train_rows & calibration_rows).any()


def test_split_rows_leaves_the_gap_out_of_both_parts():
    raw, t = _rows(np.full(10000, 50.0))
    train_rows, calibration_rows = split_rows(raw, t, share=0.10, block=20.0, gap=5.0,
                                     min_speed=5.0, period=PERIOD)
    assert (~train_rows & ~calibration_rows).any()
    nearest = np.abs(t[train_rows][:, None] - t[calibration_rows][None, :]).min()
    assert nearest > 5.0


def test_rows_within_the_gap_of_the_test_block_are_dropped():
    times = np.array([0.0, 4.0, 6.0, 20.0, 34.0, 36.0])
    kept = apart_from_test(times, start=10.0, end=30.0, gap=5.0)
    assert kept.tolist() == [True, True, False, False, False, True]
