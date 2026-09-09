import random

import numpy as np

from assemble.attack_set import attack_set
from assemble.train_set import Scale, grid_rows

SIGNALS = 17


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


def _scale():
    return Scale(np.zeros(SIGNALS, dtype=np.float32), np.ones(SIGNALS, dtype=np.float32))


def test_it_returns_a_row_for_every_grid_tick(tmp_path):
    d = attack_set([_write_log(tmp_path / "a.csv")], _scale(), random.Random(0))
    assert d["rows"].shape[1] == SIGNALS
    assert len(d["t"]) == len(d["seg"]) == len(d["label"]) == len(d["rows"])


def test_the_label_marks_the_rows_an_attack_changed(tmp_path):
    d = attack_set([_write_log(tmp_path / "a.csv")], _scale(), random.Random(0))
    assert d["attacks"], "the log should be long enough to attack"
    for a in d["attacks"]:
        assert d["label"][a["first"]] and d["label"][a["last"]]
        assert d["t"][a["first"]] >= a["start"]
        # the grid holds the last payload, so one row past the window still carries it
        assert d["t"][a["last"]] <= a["stop"] + 0.1


def test_only_the_rows_that_differ_from_the_clean_log_are_labelled(tmp_path):
    log = _write_log(tmp_path / "a.csv")
    d = attack_set([log], _scale(), random.Random(0))
    clean, _, _ = grid_rows([log])                # mean 0 and std 1 leave rows as they are
    assert len(clean) == len(d["rows"])
    assert np.array_equal((clean != d["rows"]).any(axis=1), d["label"])


def test_it_says_how_far_each_attack_moved_a_row(tmp_path):
    d = attack_set([_write_log(tmp_path / "a.csv")], _scale(), random.Random(0))
    assert all(a["moved"] > 0 for a in d["attacks"])


def test_rows_outside_every_attack_are_not_labelled(tmp_path):
    d = attack_set([_write_log(tmp_path / "a.csv")], _scale(), random.Random(0))
    covered = np.zeros(len(d["label"]), dtype=bool)
    for a in d["attacks"]:
        covered[a["first"]:a["last"] + 1] = True
    assert not d["label"][~covered].any()


def test_a_log_too_short_to_attack_still_contributes_rows(tmp_path):
    d = attack_set([_write_log(tmp_path / "a.csv", seconds=5)], _scale(), random.Random(0))
    assert len(d["rows"]) > 0
    assert d["attacks"] == []
    assert not d["label"].any()


def test_one_seed_gives_one_set(tmp_path):
    log = _write_log(tmp_path / "a.csv")
    a = attack_set([log], _scale(), random.Random(3))
    b = attack_set([log], _scale(), random.Random(3))
    assert a["attacks"] == b["attacks"]
    assert np.array_equal(a["label"], b["label"])


def test_raw_holds_the_rows_before_scaling(tmp_path):
    scale = Scale(np.full(SIGNALS, 3.0, np.float32), np.full(SIGNALS, 7.0, np.float32))
    d = attack_set([_write_log(tmp_path / "a.csv")], scale, random.Random(0))
    assert np.allclose(d["rows"], scale.apply(d["raw"]))
