import numpy as np

from assemble.train_set import grid_rows, save, scaled_rows


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
    rows, times, segments = grid_rows([_write_log(tmp_path / "a.csv", [800] * 6)])
    assert rows.ndim == 2 and rows.shape[1] == 17
    assert times.shape == segments.shape == (len(rows),)


def test_grid_rows_keeps_the_time_of_each_row(tmp_path):
    _, times, _ = grid_rows([_write_log(tmp_path / "a.csv", [800] * 6)])
    assert times.dtype == np.float64          # epoch seconds lose 0.1 s in float32
    assert np.allclose(np.diff(times), 0.1)


def test_segments_break_between_files(tmp_path):
    files = [_write_log(tmp_path / "a.csv", [800] * 6),
             _write_log(tmp_path / "b.csv", [900] * 6)]
    _, _, segments = grid_rows(files)
    assert len(set(segments)) == 2
    assert segments[0] != segments[-1]


def test_segments_break_across_a_gap(tmp_path):
    # one file, but the log jumps 30 s after the 4th sample
    log = _write_log(tmp_path / "a.csv", [800] * 10, gap_after=4, gap=30.0)
    _, times, segments = grid_rows([log])
    assert len(set(segments)) == 2, "the gap must start a new segment"
    first, second = (times[segments == s] for s in sorted(set(segments)))
    assert second[0] - first[-1] > 1.0                  # the gap is not bridged
    for run in (first, second):
        assert np.allclose(np.diff(run), 0.1)           # each segment is evenly spaced


def test_scaled_rows_standardizes_the_rows_it_was_given(tmp_path):
    log = _write_log(tmp_path / "tr.csv", [600, 800, 1000, 1200, 1400, 1600, 1800, 2000])
    data = scaled_rows([log])

    engine_speed = data["rows"][:, 0]         # first signal in SIGNALS order
    assert abs(engine_speed.mean()) < 1e-4
    assert abs(engine_speed.std() - 1.0) < 1e-4


def test_the_scale_it_fits_puts_other_rows_on_the_same_scale(tmp_path):
    train = _write_log(tmp_path / "tr.csv", [600, 800, 1000, 1200, 1400, 1600, 1800, 2000])
    other = _write_log(tmp_path / "te.csv", [900] * 6)
    scale = scaled_rows([train])["scale"]
    rows, _, _ = grid_rows([other])

    assert np.allclose(scale.undo(scale.apply(rows)), rows, atol=1e-3)


def test_scaled_rows_carries_the_time_and_segment_of_each_row(tmp_path):
    data = scaled_rows([_write_log(tmp_path / "tr.csv", [800] * 6)])
    assert len(data["t"]) == len(data["rows"])
    assert len(data["seg"]) == len(data["rows"])
    assert sorted(set(data["seg"])) == list(range(len(set(data["seg"]))))


def test_save_writes_every_array(tmp_path):
    data = scaled_rows([_write_log(tmp_path / "a.csv", [800] * 6)])
    out = tmp_path / "out"
    save(data, str(out))
    for name in data:
        assert (out / f"{name}.npy").exists() or name == "scale"
    assert np.array_equal(np.load(out / "t.npy"), data["t"])
    assert np.array_equal(np.load(out / "mean.npy"), data["scale"].mean)
