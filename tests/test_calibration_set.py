import json
import os

import numpy as np

from assemble import calibration_set
from assemble.calibration_set import calibration_blocks, seconds_from
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20

LOGS = ["part_1/a.csv", "part_1/b.csv"]


def _rows(speeds):
    """Rows carrying only a wheel speed, one per 100 ms, with their times."""
    raw = np.zeros((len(speeds), len(SIGNALS)), np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = speeds
    return raw, np.arange(len(speeds), dtype=np.float64) * 0.1


def _inside(t, blocks):
    return seconds_from(t, blocks) == 0


def test_the_blocks_hold_the_share_of_the_seconds_asked_for():
    raw, t = _rows(np.full(100000, 50.0))
    blocks = calibration_blocks(raw, t, share=0.10, block=20.0, min_speed=5.0,
                                period=0.1)
    assert abs(_inside(t, blocks).mean() - 0.10) < 0.01


def test_a_block_is_the_block_long():
    raw, t = _rows(np.full(10000, 50.0))
    blocks = calibration_blocks(raw, t, share=0.10, block=20.0, min_speed=5.0,
                                period=0.1)
    assert all(abs(last - first - 19.9) < 1e-6 for first, last in blocks)


def test_the_blocks_spread_over_the_rows():
    raw, t = _rows(np.full(100000, 50.0))
    blocks = calibration_blocks(raw, t, share=0.10, block=20.0, min_speed=5.0,
                                period=0.1)
    assert blocks[0][0] < 100.0 and blocks[-1][1] > 9000.0


def test_the_block_is_measured_in_seconds_above_min_speed():
    speeds = np.full(20000, 50.0)
    speeds[1::2] = 0.0                          # the truck stops every other row
    raw, t = _rows(speeds)
    blocks = calibration_blocks(raw, t, share=0.10, block=20.0, min_speed=5.0,
                                period=0.1)
    moving_inside = _inside(t, blocks) & (speeds > 5.0)
    assert abs(moving_inside.sum() / (speeds > 5.0).sum() - 0.10) < 0.01


def test_seconds_from_is_0_inside_a_span_and_the_distance_outside():
    times = np.array([0.0, 4.0, 10.0, 20.0, 34.0, 36.0])
    got = seconds_from(times, [[10.0, 30.0]])
    assert got.tolist() == [10.0, 6.0, 0.0, 0.0, 4.0, 6.0]


def test_seconds_from_takes_the_nearest_span():
    got = seconds_from(np.array([12.0, 18.0]), [[0.0, 10.0], [20.0, 30.0]])
    assert got.tolist() == [2.0, 2.0]


def test_seconds_from_no_span_is_infinite():
    assert np.isinf(seconds_from(np.array([1.0]), [])).all()


def _grid_and_log_split(hub, speeds, non_test_rows):
    """A grid of two logs carrying `speeds`, the first `non_test_rows` rows non-test."""
    raw, t = _rows(speeds)
    hub.files = {
        "grids/20260101-000000/meta.json": {"inputs": {"period": 0.1, "max_hold": 1.0}},
        "grids/20260101-000000/logs.json": {
            "logs": LOGS, "rows": [non_test_rows, len(t) - non_test_rows]},
        "grids/20260101-000000/grid_raw.npy": raw,
        "grids/20260101-000000/grid_t.npy": t,
        "log_splits/20260101-000000/meta.json": {
            "inputs": {"grid": "grids/20260101-000000", "min_speed": 5.0},
            "grid": {"repo": "u/d", "revision": REVISION,
                     "path": "grids/20260101-000000"}},
        "log_splits/20260101-000000/log_split.json": {
            "non_test": LOGS[:1], "test": LOGS[1:],
            "test_start": t[non_test_rows], "test_end": t[-1]}}
    return raw, t


def test_the_stage_writes_the_blocks_and_the_moving_rows_in_them(tmp_path, hub):
    raw, t = _grid_and_log_split(hub, np.full(10000, 50.0), 5000)
    made = calibration_set.main("u/d", REVISION, "log_splits/20260101-000000",
                                str(tmp_path))
    folder = tmp_path / made["path"]
    assert sorted(os.listdir(folder)) == ["blocks.json", "calibration_rows.npy",
                                          "meta.json"]
    blocks = json.loads((folder / "blocks.json").read_text())
    # BLOCK 20 s every 200 s, over the 500 s of the non-test log
    assert np.allclose(blocks, [[0.0, 19.9], [200.0, 219.9], [400.0, 419.9]])
    calibration_rows = np.load(folder / "calibration_rows.npy")
    assert np.array_equal(calibration_rows, _inside(t, blocks) & (t < 500.0))
    meta = json.loads((folder / "meta.json").read_text())
    assert meta["log_split"]["path"] == "log_splits/20260101-000000"
    assert meta["grid"]["path"] == "grids/20260101-000000"


def test_the_stage_keeps_the_stopped_rows_out(tmp_path, hub):
    speeds = np.full(10000, 50.0)
    speeds[100:150] = 3.0                       # the truck stops inside the first block
    raw, t = _grid_and_log_split(hub, speeds, 5000)
    made = calibration_set.main("u/d", REVISION, "log_splits/20260101-000000",
                                str(tmp_path))
    calibration_rows = np.load(tmp_path / made["path"] / "calibration_rows.npy")
    assert not calibration_rows[100:150].any() and calibration_rows[:100].all()


def test_the_stage_keeps_the_rows_near_the_test_span_out(tmp_path, hub):
    speeds = np.full(10000, 50.0)
    speeds[:3950] = 0.0                         # the one block runs 395.0 to 414.9
    raw, t = _grid_and_log_split(hub, speeds, 4150)
    made = calibration_set.main("u/d", REVISION, "log_splits/20260101-000000",
                                str(tmp_path))
    calibration_rows = np.load(tmp_path / made["path"] / "calibration_rows.npy")
    # the test span starts at 415, GAP is 5
    assert calibration_rows[t < 409.95].any() and not calibration_rows[t > 410.0].any()


def test_the_stage_names_a_calibration_set_of_the_same_log_split(tmp_path, hub):
    inputs = {"log_split": "log_splits/20260101-000000", "calibration": 0.10,
              "block": 20.0, "gap": 5.0}
    hub.files = {"calibration_sets/20260101-000000/meta.json": {"inputs": inputs}}
    found = calibration_set.main("u/d", REVISION, "log_splits/20260101-000000",
                                 str(tmp_path))
    assert found["path"] == "calibration_sets/20260101-000000" and hub.uploaded == []


def test_the_rows_are_the_ones_the_calibration_set_names(tmp_path, hub):
    hub.files.update({
        "calibration_sets/20260101-000000/meta.json": {
            "inputs": {},
            "log_split": {"repo": "user/data", "revision": REVISION,
                          "path": "log_splits/20260101-000000"},
            "grid": {"repo": "user/data", "revision": REVISION,
                     "path": "grids/20260101-000000"}},
        "calibration_sets/20260101-000000/calibration_rows.npy":
            np.array([False, True, False]),
        "log_splits/20260101-000000/meta.json": {"inputs": {"min_speed": 5.0}},
        "grids/20260101-000000/meta.json": {"inputs": {"period": 0.1}},
        "grids/20260101-000000/grid_raw.npy":
            np.array([[10.0], [30.0], [50.0]], np.float32),
        "grids/20260101-000000/grid_t.npy": np.array([0.0, 0.1, 0.2]),
        "grids/20260101-000000/logs.json": {"logs": ["a.csv"], "rows": [3]},
    })
    got = calibration_set.fetch_calibration_set(
        "user/data", REVISION, "calibration_sets/20260101-000000", str(tmp_path))

    assert got["calibration"].tolist() == [[30.0]]
    assert got["min_speed"] == 5.0, "the log split decides the speed, not Settings"
