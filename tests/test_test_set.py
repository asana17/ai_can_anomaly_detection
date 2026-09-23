import json
import os
import random

import numpy as np
import pytest

from assemble import test_set
from assemble.test_set import grid_rows_injected, inject_frames
from assemble.grid import grid_rows
from preprocess.features import signal_state
from preprocess.frames.can_log_loader import CanFrame

REVISION = "ab" * 20

SIGNALS = 17
PERIOD, MAX_HOLD = 0.1, 1.0


def _ts(t):
    return f"2020-11-23 08:{int(t) // 60:02d}:{int(t) % 60:02d}.{round((t % 1) * 1e6):06d}"


def _write_log(path, seconds=40, period=0.1):
    """A log where the speed climbs, so any two moments differ."""
    lines = ["timestamp;id;dlc;data"]
    for i in range(int(seconds / period)):
        ts, kmh = _ts(i * period), i * period
        raw = round(kmh / 0.00390625)
        rpm = round((600 + i) / 0.125)
        lines += [
            f"{ts};0x18F004E6;8;0;0;0;{rpm & 0xFF};{(rpm >> 8) & 0xFF};0;0;0",
            f"{ts};0x18F003E6;8;0;0;0;0;0;0;0;0",
            f"{ts};0x18FEF1E6;8;0;{raw & 0xFF};{(raw >> 8) & 0xFF};0;0;0;0;0",
            f"{ts};0x18FEF2E6;8;10;0;255;255;255;255;255;255",
            f"{ts};0x18F009E6;8;127;125;96;127;125;135;127;255",
            f"{ts};0x18F001E6;8;207;0;207;255;255;255;255;255",
            f"{ts};0x18FE6CE6;8;0;0;192;192;0;0;{raw & 0xFF};{(raw >> 8) & 0xFF}",
            f"{ts};0x18F002E6;8;205;32;28;0;252;32;28;255",
            f"{ts};0x18F005E6;8;137;0;0;137;0;0;0;0",
        ]
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def _rows_before_attack(logs):
    """Each log's rows before any attack, by time, as a grid holds them."""
    kept = {}
    for log in logs:
        raw, times, _ = grid_rows([log], period=PERIOD, max_hold=MAX_HOLD)
        kept[log] = dict(zip(times, raw))
    return lambda log: kept[log]


def _injected(logs, seed=0):
    """The rows of `logs` with one attack each, drawn from `seed`."""
    before = _rows_before_attack(logs)
    injected = inject_frames(logs, random.Random(seed), rows_before_attack=before,
                             period=PERIOD, max_hold=MAX_HOLD, min_speed=5.0)
    return grid_rows_injected(injected)


def test_donors_are_spread_over_the_logs_that_move():
    seconds = {"a": 10.0, "b": 0.0, "c": 5.0, "d": 0.0, "e": 8.0}
    assert test_set.donor_logs(list(seconds), seconds, 2) == ["a", "c"]
    assert test_set.donor_logs(list(seconds), seconds, 3) == ["a", "c", "e"]


def test_rows_before_the_attack_from_another_grid_are_refused(tmp_path):
    log = _write_log(tmp_path / "a.csv")
    shifted = {t + 0.05: row for t, row in _rows_before_attack([log])(log).items()}
    with pytest.raises(ValueError):
        list(inject_frames([log], random.Random(0), rows_before_attack=lambda _: shifted,
                           period=PERIOD, max_hold=MAX_HOLD, min_speed=5.0))


def test_it_returns_a_row_for_every_grid_tick(tmp_path):
    d = _injected([_write_log(tmp_path / "a.csv")])
    assert d["raw"].shape[1] == SIGNALS
    assert len(d["t"]) == len(d["seg"]) == len(d["label"]) == len(d["raw"])


def test_the_label_marks_the_rows_an_attack_changed(tmp_path):
    d = _injected([_write_log(tmp_path / "a.csv")])
    assert d["attacks"], "the log should be long enough to attack"
    for a in d["attacks"]:
        assert d["label"][a["first"]] and d["label"][a["last"]]
        assert d["t"][a["first"]] >= a["start"]
        # the grid holds the last payload, so one row past the window still carries it
        assert d["t"][a["last"]] <= a["stop"] + 0.1


def test_every_changed_grid_row_stays_moving(tmp_path):
    log = _write_log(tmp_path / "a.csv")
    d = _injected([log])
    assert d["attacks"]
    wheel = signal_state.SIGNALS.index("wheel_speed")
    assert np.all(d["wheel"][d["label"]] > 5.0)
    assert np.all(d["raw"][d["label"], wheel] > 5.0)


def test_a_replay_that_stops_a_changed_row_is_not_kept(tmp_path, monkeypatch):
    def stopping(frames, rng, **kwargs):
        start = frames[0].timestamp + 20.0
        hurt = [CanFrame(f.timestamp, f.can_id, bytes(8))
                if f.can_id == 0x18FEF1E6 and start <= f.timestamp <= start + 2.0 else f
                for f in frames]
        return hurt, dict(pgn=65265, start=start, stop=start + 2.0, source=0.0)

    monkeypatch.setattr(test_set, "random_replay", stopping)
    log = _write_log(tmp_path / "a.csv")
    [(_, frames, hurt, rows, attack)] = inject_frames(
        [log], random.Random(0), rows_before_attack=_rows_before_attack([log]),
        period=PERIOD, max_hold=MAX_HOLD, min_speed=5.0)
    assert attack is None
    assert hurt == frames
    assert not rows["label"].any()


def test_only_the_rows_that_differ_from_the_clean_log_are_labelled(tmp_path):
    log = _write_log(tmp_path / "a.csv")
    d = _injected([log])
    # mean 0 and std 1 leave rows as they are
    clean, _, _ = grid_rows([log], period=PERIOD, max_hold=MAX_HOLD)
    assert len(clean) == len(d["raw"])
    assert np.array_equal((clean != d["raw"]).any(axis=1), d["label"])


def test_rows_outside_every_attack_are_not_labelled(tmp_path):
    d = _injected([_write_log(tmp_path / "a.csv")])
    covered = np.zeros(len(d["label"]), dtype=bool)
    for a in d["attacks"]:
        covered[a["first"]:a["last"] + 1] = True
    assert not d["label"][~covered].any()


def test_a_signal_the_truck_sends_as_not_available_is_not_labelled(tmp_path):
    path = tmp_path / "a.csv"
    _write_log(path)
    path.write_text(path.read_text().replace(";0x18F001E6;8;207;0;", ";0x18F001E6;8;207;255;"))
    d = _injected([str(path)])
    clean, _, _ = grid_rows([str(path)], period=PERIOD, max_hold=MAX_HOLD)
    assert np.isnan(clean[:, signal_state.SIGNALS.index("brake_pedal")]).all()
    differs = [not np.array_equal(c, r, equal_nan=True) for c, r in zip(clean, d["raw"])]
    assert d["label"].tolist() == differs
    assert not d["label"].all()


def test_a_log_too_short_to_attack_still_contributes_rows(tmp_path):
    d = _injected([_write_log(tmp_path / "a.csv", seconds=5)], 0)
    assert len(d["raw"]) > 0
    assert d["attacks"] == []
    assert not d["label"].any()


def test_one_seed_gives_one_set(tmp_path):
    log = _write_log(tmp_path / "a.csv")
    a = _injected([log], 3)
    b = _injected([log], 3)
    assert a["attacks"] == b["attacks"]
    assert np.array_equal(a["label"], b["label"])


def test_wheel_holds_the_speed_before_the_attack(tmp_path):
    log = _write_log(tmp_path / "a.csv")
    d = _injected([log])
    clean, _, _ = grid_rows([log], period=PERIOD, max_hold=MAX_HOLD)
    assert np.array_equal(d["wheel"], clean[:, signal_state.SIGNALS.index("wheel_speed")])


def _hub_files(tmp_path, hub, logs):
    """A grid and a log split over `logs`, with the last log as the test log."""
    raw, times, _ = grid_rows(logs, period=PERIOD, max_hold=MAX_HOLD)
    counts = [len(grid_rows([log], period=PERIOD, max_hold=MAX_HOLD)[0]) for log in logs]
    names = [os.path.relpath(log, tmp_path) for log in logs]
    hub.files = {
        "grids/20260101-000000/meta.json": {"inputs": {"period": PERIOD,
                                                       "max_hold": MAX_HOLD}},
        "grids/20260101-000000/logs.json": {"logs": names, "rows": counts},
        "grids/20260101-000000/grid_raw.npy": raw,
        "grids/20260101-000000/grid_t.npy": times,
        "log_splits/20260101-000000/meta.json": {
            "inputs": {"grid": "grids/20260101-000000", "min_speed": 5.0},
            "grid": {"repo": "u/d", "revision": REVISION,
                     "path": "grids/20260101-000000"}},
        "log_splits/20260101-000000/log_split.json": {
            "non_test": names[:-1], "test": names[-1:],
            "test_start": 0.0, "test_end": 0.0},
        "log_splits/20260101-000000/seconds.json": {name: 35.0 for name in names}}


def test_the_stage_writes_the_rows_the_labels_and_the_frames(tmp_path, hub):
    logs = [_write_log(tmp_path / f"{n}.csv") for n in "ab"]
    _hub_files(tmp_path, hub, logs)
    made = test_set.main("u/d", REVISION, "log_splits/20260101-000000", str(tmp_path),
                         str(tmp_path / "local"))
    folder = tmp_path / "local" / made["path"]
    label = np.load(folder / "attacked_label.npy")
    assert np.load(folder / "attacked_raw.npy").shape == (len(label), SIGNALS)
    attacks = json.loads((folder / "injected.json").read_text())
    assert [a["log"] for a in attacks] == ["b.csv"]
    assert label[attacks[0]["first"]] and label[attacks[0]["last"]]
    assert len(list((folder / "frames").glob("*.parquet"))) == 1
    meta = json.loads((folder / "meta.json").read_text())
    assert meta["grid"]["path"] == "grids/20260101-000000"


def test_the_stage_refuses_a_log_split_where_no_non_test_log_moves(tmp_path, hub):
    logs = [_write_log(tmp_path / f"{n}.csv") for n in "ab"]
    _hub_files(tmp_path, hub, logs)
    hub.files["log_splits/20260101-000000/seconds.json"] = {"a.csv": 0.0, "b.csv": 35.0}
    with pytest.raises(ValueError, match="no non-test log moves"):
        test_set.main("u/d", REVISION, "log_splits/20260101-000000", str(tmp_path),
                      str(tmp_path / "local"))


def test_the_stage_names_a_test_set_of_the_same_log_split(tmp_path, hub):
    inputs = {"log_split": "log_splits/20260101-000000", "seed": 0, "donors": 24}
    hub.files = {"test_sets/20260101-000000/meta.json": {"inputs": inputs}}
    found = test_set.main("u/d", REVISION, "log_splits/20260101-000000",
                          str(tmp_path), str(tmp_path / "local"))
    assert found["path"] == "test_sets/20260101-000000" and hub.uploaded == []
