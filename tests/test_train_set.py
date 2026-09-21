import json
import os

import numpy as np
import pytest

from assemble import train_set
from assemble.grid import grid_rows
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


LOGS = ["part_1/a.csv", "part_1/b.csv"]
ENGINE = SIGNALS.index("engine_speed")


@pytest.fixture(autouse=True)
def _rules_hit_the_rows_with_an_engine_speed(monkeypatch):
    """The rows `_rows` makes carry only a wheel speed, which the real rules would hit."""
    monkeypatch.setattr(train_set, "rule_hits", lambda raw, settings: raw[:, ENGINE] > 0)


def _grid_and_calibration_set(hub, speeds, test_start, hit=slice(0),
                              blocks=((100.0, 119.9),)):
    """A grid of two logs carrying `speeds`, the first non-test, and a calibration set.

    The rows in `hit` are the ones a rule hits, and `blocks` the calibration blocks.
    """
    raw, t = _rows(speeds)
    raw[hit, ENGINE] = 1000.0
    half = len(t) // 2
    where = {"repo": "u/d", "revision": REVISION}
    hub.files = {
        "grids/20260101-000000/meta.json": {"inputs": {"period": 0.1, "max_hold": 1.0}},
        "grids/20260101-000000/logs.json": {"logs": LOGS, "rows": [half, len(t) - half]},
        "grids/20260101-000000/grid_raw.npy": raw,
        "grids/20260101-000000/grid_t.npy": t,
        "log_splits/20260101-000000/meta.json": {
            "inputs": {"grid": "grids/20260101-000000", "min_speed": 5.0},
            "grid": dict(where, path="grids/20260101-000000")},
        "log_splits/20260101-000000/log_split.json": {
            "non_test": LOGS[:1], "test": LOGS[1:],
            "test_start": test_start, "test_end": 999.9},
        "calibration_sets/20260101-000000/meta.json": {
            "inputs": {},
            "log_split": dict(where, path="log_splits/20260101-000000"),
            "grid": dict(where, path="grids/20260101-000000")},
        "calibration_sets/20260101-000000/blocks.json": [list(b) for b in blocks]}
    return raw, t, half


def _train_set(tmp_path):
    return train_set.main("u/d", REVISION, "calibration_sets/20260101-000000",
                          str(tmp_path))


def test_the_stage_writes_which_rows_train(tmp_path, hub):
    raw, t, half = _grid_and_calibration_set(hub, np.full(10000, 50.0), 600.0)
    made = _train_set(tmp_path)
    folder = tmp_path / made["path"]
    assert sorted(os.listdir(folder)) == ["meta.json", "train_rows.npy"]
    train_rows = np.load(folder / "train_rows.npy")
    assert len(train_rows) == len(raw)
    assert not train_rows[half:].any() and train_rows.any()
    meta = json.loads((folder / "meta.json").read_text())
    assert meta["calibration_set"]["path"] == "calibration_sets/20260101-000000"
    assert meta["log_split"]["path"] == "log_splits/20260101-000000"
    assert meta["grid"]["path"] == "grids/20260101-000000"


def test_the_stage_keeps_the_rows_near_a_calibration_block_out(tmp_path, hub):
    raw, t, half = _grid_and_calibration_set(hub, np.full(10000, 50.0), 600.0)
    made = _train_set(tmp_path)
    train_rows = np.load(tmp_path / made["path"] / "train_rows.npy")
    near = (t > 94.95) & (t < 125.0)            # the block is 100 to 119.9, GAP is 5
    assert not train_rows[near].any()
    assert train_rows[(t < 94.9) | ((t > 125.0) & (t < 500.0))].all()


def test_the_stage_keeps_the_rows_near_the_test_block_out(tmp_path, hub):
    raw, t, half = _grid_and_calibration_set(hub, np.full(10000, 50.0), 500.0)
    made = _train_set(tmp_path)
    train_rows = np.load(tmp_path / made["path"] / "train_rows.npy")
    near = (t > 495.0) & (t < 500.0)            # the test span starts at 500, GAP is 5
    assert near.sum() > 10 and not train_rows[near].any()
    assert train_rows[t < 490.0].any()


def test_the_stage_keeps_the_slow_rows_out_of_train(tmp_path, hub):
    speeds = np.full(10000, 50.0)
    speeds[1000:2000] = 3.0
    raw, t, half = _grid_and_calibration_set(hub, speeds, 600.0, blocks=())
    made = _train_set(tmp_path)
    train_rows = np.load(tmp_path / made["path"] / "train_rows.npy")
    assert not train_rows[1000:2000].any() and train_rows[:1000].any()


def test_the_stage_keeps_the_rows_a_rule_hits_out_of_train(tmp_path, hub):
    raw, t, half = _grid_and_calibration_set(hub, np.full(10000, 50.0), 600.0,
                                             hit=slice(1000, 2000), blocks=())
    made = _train_set(tmp_path)
    folder = tmp_path / made["path"]
    train_rows = np.load(folder / "train_rows.npy")
    assert not train_rows[1000:2000].any() and train_rows[:1000].any()
    rule_hits = json.loads((folder / "meta.json").read_text())["rule_hits"]
    assert rule_hits["hit"] > 0
    assert rule_hits["rows"] - rule_hits["hit"] == train_rows.sum()


def test_the_stage_names_a_train_set_of_the_same_calibration_set(tmp_path, hub):
    inputs = {"calibration_set": "calibration_sets/20260101-000000", "gap": 5.0}
    hub.files = {"train_sets/20260101-000000/meta.json": {"inputs": inputs}}
    found = _train_set(tmp_path)
    assert found["path"] == "train_sets/20260101-000000" and hub.uploaded == []


def test_read_train_set_reads_the_rows_back(tmp_path):
    np.save(tmp_path / "train_rows.npy", np.array([True, False]))

    assert train_set.read_train_set(str(tmp_path)).tolist() == [True, False]


def test_the_rows_are_the_ones_the_train_set_names(tmp_path, hub):
    hub.files.update({
        "train_sets/20260101-000000/meta.json": {
            "inputs": {},
            "calibration_set": {"repo": "user/data", "revision": REVISION,
                                "path": "calibration_sets/20260101-000000"},
            "log_split": {"repo": "user/data", "revision": REVISION,
                          "path": "log_splits/20260101-000000"},
            "grid": {"repo": "user/data", "revision": REVISION,
                     "path": "grids/20260101-000000"}},
        "train_sets/20260101-000000/train_rows.npy": np.array([True, False, False]),
        "log_splits/20260101-000000/meta.json": {"inputs": {"min_speed": 5.0}},
        "grids/20260101-000000/meta.json": {"inputs": {"period": 0.1}},
        "grids/20260101-000000/grid_raw.npy":
            np.array([[10.0], [30.0], [50.0]], np.float32),
        "grids/20260101-000000/grid_t.npy": np.array([0.0, 0.1, 0.2]),
        "grids/20260101-000000/logs.json": {"logs": ["a.csv"], "rows": [3]},
    })
    got = train_set.fetch_train_set("user/data", REVISION, "train_sets/20260101-000000",
                                    str(tmp_path))

    assert got["train"].tolist() == [[10.0]]
    assert got["min_speed"] == 5.0, "the log split decides the speed, not Settings"
    calibration = got["dataset"]["calibration_set"]
    assert calibration["path"] == "calibration_sets/20260101-000000"
