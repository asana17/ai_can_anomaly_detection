import numpy as np
import pytest

from assemble.split import WHEEL, moving, seconds_above, split, split_rows


def test_the_last_fold_tests_on_the_last_block():
    logs = [f"{i:03d}.csv" for i in range(100)]
    train, test = split({p: 1.0 for p in logs}, 4, 3)
    assert (train, test) == (logs[:75], logs[75:])


def test_the_first_fold_tests_on_the_first_block():
    logs = [f"{i:03d}.csv" for i in range(100)]
    train, test = split({p: 1.0 for p in logs}, 4, 0)
    assert (train, test) == (logs[25:], logs[:25])


def test_a_middle_fold_trains_on_both_sides():
    logs = [f"{i:03d}.csv" for i in range(100)]
    train, test = split({p: 1.0 for p in logs}, 4, 1)
    assert (train, test) == (logs[:25] + logs[50:], logs[25:50])


def test_a_fold_outside_the_blocks_is_refused():
    for fold in (-1, 4):
        with pytest.raises(ValueError):
            split({"a.csv": 1.0}, 4, fold)


def test_orders_by_filename_before_splitting():
    logs = ["c.csv", "a.csv", "b.csv"]  # not in order
    train, test = split({p: 1.0 for p in logs}, 3, 2)
    assert train + test == ["a.csv", "b.csv", "c.csv"]


def test_every_fold_covers_everything_once():
    logs = [f"{i:04d}.csv" for i in range(50)]
    for fold in range(4):
        train, test = split({p: 1.0 for p in logs}, 4, fold)
        assert sorted(train + test) == sorted(logs)


def test_the_seconds_size_the_parts_instead_of_the_log_count():
    logs = [f"{i:03d}.csv" for i in range(10)]
    seconds = {p: (100.0 if i < 2 else 0.0) for i, p in enumerate(logs)}
    seconds["009.csv"] = 100.0                    # the only moving traffic late on
    train, test = split(seconds, 3, 0)
    assert test == ["000.csv"]                    # a third of the moving traffic
    assert train == [f"{i:03d}.csv" for i in range(1, 10)]


def test_split_gives_test_nothing_when_no_log_holds_a_scoreable_second():
    logs = [f"{i:03d}.csv" for i in range(10)]
    train, test = split({p: 0.0 for p in logs}, 2, 1)
    assert (train, test) == (logs, [])


def test_seconds_above_counts_only_readings_over_the_minimum(tmp_path):
    def ccvs1(kmh):
        raw = round(kmh / 0.00390625)
        return f"2020-11-23 08:00:00.000000;0x18FEF1E6;8;0;{raw & 0xFF};{(raw >> 8) & 0xFF};0;0;0;0;0"

    log = tmp_path / "a.csv"
    log.write_text("\n".join(["timestamp;id;dlc;data"]
                             + [ccvs1(kmh) for kmh in (0.0, 4.0, 6.0, 80.0)]
                             + ["2020-11-23 08:00:00.000000;0x18F004E6;8;0;0;0;0;0;0;0;0"]) + "\n")
    assert seconds_above([str(log)], 5.0) == {str(log): 0.2}   # two readings, 100 ms apart


def _rows(speeds):
    """Rows carrying only a wheel speed, one per 100 ms, with their times."""
    raw = np.zeros((len(speeds), 17), np.float32)
    raw[:, WHEEL] = speeds
    return raw, np.arange(len(speeds), dtype=np.float64) * 0.1


def test_moving_is_the_rows_over_the_speed_given():
    raw, _ = _rows([0.0, 4.9, 5.0, 5.1, 80.0])
    assert moving(raw, 5.0).tolist() == [False, False, False, True, True]


def test_split_rows_gives_calibration_the_share_of_the_seconds_asked_for():
    raw, t = _rows(np.full(100000, 50.0))
    train_rows, calibration_rows = split_rows(raw, t, 0.10, 20.0, 0.0, 5.0)
    assert abs(calibration_rows.mean() - 0.10) < 0.01


def test_split_rows_cuts_calibration_into_windows_of_the_block_length():
    raw, t = _rows(np.full(10000, 50.0))
    _, calibration_rows = split_rows(raw, t, 0.10, 20.0, 0.0, 5.0)
    edges = np.flatnonzero(np.diff(np.concatenate(
        [[0], calibration_rows.astype(np.int8), [0]])))
    assert set((edges[1::2] - edges[::2]).tolist()) == {200}   # 20 s at 100 ms


def test_split_rows_spreads_the_windows_over_the_period():
    raw, t = _rows(np.full(100000, 50.0))
    _, calibration_rows = split_rows(raw, t, 0.10, 20.0, 0.0, 5.0)
    at = np.flatnonzero(calibration_rows)
    assert at[0] < 1000 and at[-1] > 90000


def test_split_rows_never_calibrates_on_a_stopped_row():
    speeds = np.full(20000, 50.0)
    speeds[1::2] = 0.0                          # the truck stops every other row
    raw, t = _rows(speeds)
    _, calibration_rows = split_rows(raw, t, 0.10, 20.0, 0.0, 5.0)
    assert calibration_rows.any() and not (calibration_rows & (speeds == 0.0)).any()


def test_split_rows_measures_the_block_in_seconds_above_min_speed():
    speeds = np.full(20000, 50.0)
    speeds[1::2] = 0.0
    raw, t = _rows(speeds)
    _, calibration_rows = split_rows(raw, t, 0.10, 20.0, 0.0, 5.0)
    assert abs(calibration_rows.sum() / (speeds > 5.0).sum() - 0.10) < 0.01


def test_split_rows_puts_no_row_in_both_parts():
    raw, t = _rows(np.full(10000, 50.0))
    train_rows, calibration_rows = split_rows(raw, t, 0.10, 20.0, 5.0, 5.0)
    assert not (train_rows & calibration_rows).any()


def test_split_rows_leaves_the_gap_out_of_both_parts():
    raw, t = _rows(np.full(10000, 50.0))
    train_rows, calibration_rows = split_rows(raw, t, 0.10, 20.0, 5.0, 5.0)
    assert (~train_rows & ~calibration_rows).any()
    nearest = np.abs(t[train_rows][:, None] - t[calibration_rows][None, :]).min()
    assert nearest > 5.0
