from assemble.datasets import build, vectorize


def _ts(t):
    whole = int(t)
    frac = round((t - whole) * 1_000_000)
    return f"2020-11-23 08:00:{whole:02d}.{frac:06d}"


def _write_log(path, rpms, period=0.1):
    lines = ["timestamp;id;dlc;data"]
    for i, rpm in enumerate(rpms):
        ts = _ts(i * period)
        raw = round(rpm / 0.125)
        lines.append(f"{ts};0x18F004E6;8;0;0;0;{raw & 0xFF};{(raw >> 8) & 0xFF};0;0;0")  # EEC1
        lines.append(f"{ts};0x18F003E6;8;0;0;0;0;0;0;0;0")  # EEC2
        lines.append(f"{ts};0x18FEF1E6;8;0;0;0;0;0;0;0;0")  # CCVS1
        lines.append(f"{ts};0x18FEF2E6;8;10;0;255;255;255;255;255;255")  # LFE1
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def test_vectorize_returns_2d_signal_rows(tmp_path):
    arr = vectorize([_write_log(tmp_path / "a.csv", [800] * 6)], period=0.1)
    assert arr.ndim == 2 and arr.shape[1] == 7


def test_build_standardizes_train_and_reuses_stats(tmp_path):
    train = _write_log(tmp_path / "tr.csv", [600, 800, 1000, 1200, 1400, 1600, 1800, 2000])
    val = _write_log(tmp_path / "va.csv", [900] * 6)
    test = _write_log(tmp_path / "te.csv", [900] * 6)
    data = build([train], [val], [test], period=0.1)

    engine_speed = data["train"][:, 0]        # first signal in SIGNALS order
    assert abs(engine_speed.mean()) < 1e-4
    assert abs(engine_speed.std() - 1.0) < 1e-4
    assert data["val"].shape[1] == 7          # normalized with train's stats
