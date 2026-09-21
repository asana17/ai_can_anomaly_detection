import json

import numpy as np
import pytest

from assemble import train_set
from assemble.grid import grid_rows
from assemble.train_set import apart_from_test, split_rows
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20

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


def _rows(speeds):
    """Rows carrying only a wheel speed, one per 100 ms, with their times."""
    raw = np.zeros((len(speeds), 17), np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = speeds
    return raw, np.arange(len(speeds), dtype=np.float64) * 0.1


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


LOGS = ["part_1/a.csv", "part_1/b.csv"]
ENGINE = SIGNALS.index("engine_speed")


@pytest.fixture(autouse=True)
def _rules_hit_the_rows_with_an_engine_speed(monkeypatch):
    """The rows `_rows` makes carry only a wheel speed, which the real rules would hit."""
    monkeypatch.setattr(train_set, "rule_hits", lambda raw, settings: raw[:, ENGINE] > 0)


def _grid_and_split(hub, speeds, test_start, test_end, hit=slice(0)):
    """A grid of two logs carrying `speeds`, split with the first log as train.

    The rows in `hit` are the ones a rule hits.
    """
    raw, t = _rows(speeds)
    raw[hit, ENGINE] = 1000.0
    half = len(t) // 2
    hub.files = {
        "grids/20260101-000000/meta.json": {"inputs": {"period": 0.1, "max_hold": 1.0}},
        "grids/20260101-000000/logs.json": {"logs": LOGS, "rows": [half, len(t) - half]},
        "grids/20260101-000000/grid_raw.npy": raw,
        "grids/20260101-000000/grid_t.npy": t,
        "splits/20260101-000000/meta.json": {
            "inputs": {"grid": "grids/20260101-000000", "min_speed": 5.0},
            "grid": {"repo": "u/d", "revision": REVISION,
                     "path": "grids/20260101-000000"}},
        "splits/20260101-000000/split.json": {
            "train": LOGS[:1], "test": LOGS[1:],
            "test_start": test_start, "test_end": test_end}}
    return raw, t, half


def test_the_stage_writes_which_rows_train_and_calibrate(tmp_path, hub):
    raw, t, half = _grid_and_split(hub, np.full(10000, 50.0), 600.0, 999.9)
    made = train_set.main("u/d", REVISION, "splits/20260101-000000", str(tmp_path))
    folder = tmp_path / made["path"]
    train_rows = np.load(folder / "train_rows.npy")
    calibration_rows = np.load(folder / "calibration_rows.npy")
    assert len(train_rows) == len(raw)
    assert not train_rows[half:].any() and not calibration_rows[half:].any()
    assert train_rows.any() and calibration_rows.any()
    assert not (train_rows & calibration_rows).any()
    meta = json.loads((folder / "meta.json").read_text())
    assert meta["split"]["path"] == "splits/20260101-000000"
    assert meta["grid"]["path"] == "grids/20260101-000000"


def test_the_stage_keeps_the_rows_near_the_test_block_out_of_both(tmp_path, hub):
    raw, t, half = _grid_and_split(hub, np.full(10000, 50.0), 500.0, 999.9)
    made = train_set.main("u/d", REVISION, "splits/20260101-000000", str(tmp_path))
    folder = tmp_path / made["path"]
    kept = (np.load(folder / "train_rows.npy")
            | np.load(folder / "calibration_rows.npy"))
    near = (t > 495.0) & (t < 500.0)            # the test block starts at 500, GAP is 5
    assert near.sum() > 10 and not kept[near].any() and kept[t < 490.0].any()


def test_the_stage_keeps_the_slow_rows_out_of_train(tmp_path, hub):
    speeds = np.full(10000, 50.0)
    speeds[1000:2000] = 3.0
    raw, t, half = _grid_and_split(hub, speeds, 600.0, 999.9)
    made = train_set.main("u/d", REVISION, "splits/20260101-000000", str(tmp_path))
    train_rows = np.load(tmp_path / made["path"] / "train_rows.npy")
    assert not train_rows[1000:2000].any() and train_rows[:1000].any()


def test_the_stage_keeps_the_rows_a_rule_hits_out_of_train(tmp_path, hub):
    raw, t, half = _grid_and_split(hub, np.full(10000, 50.0), 600.0, 999.9,
                                   hit=slice(1000, 2000))
    made = train_set.main("u/d", REVISION, "splits/20260101-000000", str(tmp_path))
    folder = tmp_path / made["path"]
    train_rows = np.load(folder / "train_rows.npy")
    assert not train_rows[1000:2000].any() and train_rows[:1000].any()
    rule_hits = json.loads((folder / "meta.json").read_text())["rule_hits"]
    assert rule_hits["hit"] > 0
    assert rule_hits["rows"] - rule_hits["hit"] == train_rows.sum()


def test_the_stage_names_a_train_set_of_the_same_split(tmp_path, hub):
    inputs = {"split": "splits/20260101-000000", "calibration": 0.10, "block": 20.0,
              "gap": 5.0}
    hub.files = {"train_sets/20260101-000000/meta.json": {"inputs": inputs}}
    found = train_set.main("u/d", REVISION, "splits/20260101-000000", str(tmp_path))
    assert found["path"] == "train_sets/20260101-000000" and hub.uploaded == []


def test_read_train_set_reads_the_rows_back(tmp_path):
    np.save(tmp_path / "train_rows.npy", np.array([True, False]))
    np.save(tmp_path / "calibration_rows.npy", np.array([False, True]))
    train_rows, calibration_rows = train_set.read_train_set(str(tmp_path))

    assert train_rows.tolist() == [True, False]
    assert calibration_rows.tolist() == [False, True]


def test_the_rows_are_the_ones_the_train_set_names(tmp_path, hub):
    hub.files.update({
        "train_sets/20260101-000000/meta.json": {
            "inputs": {},
            "split": {"repo": "user/data", "revision": REVISION,
                      "path": "splits/20260101-000000"},
            "grid": {"repo": "user/data", "revision": REVISION,
                     "path": "grids/20260101-000000"}},
        "train_sets/20260101-000000/train_rows.npy": np.array([True, False, False]),
        "train_sets/20260101-000000/calibration_rows.npy":
            np.array([False, True, False]),
        "splits/20260101-000000/meta.json": {"inputs": {"min_speed": 5.0}},
        "grids/20260101-000000/meta.json": {"inputs": {"period": 0.1}},
        "grids/20260101-000000/grid_raw.npy":
            np.array([[10.0], [30.0], [50.0]], np.float32),
        "grids/20260101-000000/grid_t.npy": np.array([0.0, 0.1, 0.2]),
        "grids/20260101-000000/logs.json": {"logs": ["a.csv"], "rows": [3]},
    })
    got = train_set.fetch_train_set("user/data", REVISION, "train_sets/20260101-000000",
                                    str(tmp_path))

    assert got["train"].tolist() == [[10.0]], "the third row is in neither part"
    assert got["calibration"].tolist() == [[30.0]]
    assert got["min_speed"] == 5.0, "the split decides the speed, not Settings"
