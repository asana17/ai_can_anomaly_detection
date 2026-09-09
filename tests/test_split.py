from assemble.split import driving_time, hold_out, split


def test_split_fraction_sizes():
    logs = [f"{i:03d}.csv" for i in range(100)]
    train, test = split(logs, 0.70)
    assert (len(train), len(test)) == (70, 30)


def test_orders_by_filename_before_splitting():
    logs = ["c.csv", "a.csv", "b.csv"]  # not in order
    train, test = split(logs, 0.34)
    assert train + test == ["a.csv", "b.csv", "c.csv"]


def test_the_two_parts_cover_everything_once():
    logs = [f"{i:04d}.csv" for i in range(50)]
    train, test = split(logs, 0.70)
    assert train + test == sorted(logs)


def test_a_weight_sizes_the_parts_instead_of_the_log_count():
    logs = [f"{i:03d}.csv" for i in range(10)]
    weight = {p: (100 if i < 2 else 0) for i, p in enumerate(logs)}
    weight["009.csv"] = 100                       # the only moving traffic late on
    train, test = split(logs, 0.34, weight)
    assert train == ["000.csv"]                   # a third of the moving traffic
    assert test == [f"{i:03d}.csv" for i in range(1, 10)]


def test_all_weights_zero_falls_back_to_the_log_count():
    logs = [f"{i:03d}.csv" for i in range(10)]
    assert split(logs, 0.50, {p: 0 for p in logs}) == split(logs, 0.50)


def test_driving_time_counts_only_readings_above_the_minimum(tmp_path):
    def ccvs1(kmh):
        raw = round(kmh / 0.00390625)
        return f"2020-11-23 08:00:00.000000;0x18FEF1E6;8;0;{raw & 0xFF};{(raw >> 8) & 0xFF};0;0;0;0;0"

    log = tmp_path / "a.csv"
    log.write_text("\n".join(["timestamp;id;dlc;data"]
                             + [ccvs1(kmh) for kmh in (0.0, 4.0, 6.0, 80.0)]
                             + ["2020-11-23 08:00:00.000000;0x18F004E6;8;0;0;0;0;0;0;0;0"]) + "\n")
    assert driving_time([str(log)]) == {str(log): 0.2}   # two readings, 100 ms apart


def test_hold_out_takes_contiguous_blocks_spread_over_the_period():
    logs = [f"{i:03d}.csv" for i in range(100)]
    kept, held = hold_out(logs, 0.20, blocks=4)
    assert len(held) == 20 and len(kept) == 80
    runs = [held[0]]
    for a, b in zip(held, held[1:]):
        if int(b[:3]) != int(a[:3]) + 1:
            runs.append(b)
    assert len(runs) == 4, "each block has to be one unbroken stretch"
    assert int(runs[0][:3]) < 25 and int(runs[-1][:3]) > 70


def test_hold_out_drops_the_logs_beside_each_block():
    logs = [f"{i:03d}.csv" for i in range(100)]
    kept, held = hold_out(logs, 0.10, blocks=2, gap=3)
    assert len(held) == 10
    assert len(kept) == 100 - 10 - 2 * 2 * 3
    assert not (set(kept) & set(held))
    for h in held:
        near = {f"{int(h[:3]) + d:03d}.csv" for d in (-1, 1)}
        assert not (near & set(kept)), "a kept log must not touch a held one"


def test_hold_out_without_a_gap_keeps_every_log():
    logs = [f"{i:03d}.csv" for i in range(40)]
    kept, held = hold_out(logs, 0.25, blocks=2)
    assert sorted(kept + held) == logs
