from assemble.split import hold_out, moving_frames, split


def test_split_fraction_sizes():
    files = [f"{i:03d}.csv" for i in range(100)]
    train, test = split(files, 0.70)
    assert (len(train), len(test)) == (70, 30)


def test_orders_by_filename_before_splitting():
    files = ["c.csv", "a.csv", "b.csv"]  # not in order
    train, test = split(files, 0.34)
    assert train + test == ["a.csv", "b.csv", "c.csv"]


def test_the_two_parts_cover_everything_once():
    files = [f"{i:04d}.csv" for i in range(50)]
    train, test = split(files, 0.70)
    assert train + test == sorted(files)


def test_a_weight_sizes_the_parts_instead_of_the_file_count():
    files = [f"{i:03d}.csv" for i in range(10)]
    weight = {p: (100 if i < 2 else 0) for i, p in enumerate(files)}
    weight["009.csv"] = 100                       # the only moving traffic late on
    train, test = split(files, 0.34, weight)
    assert train == ["000.csv"]                   # a third of the moving traffic
    assert test == [f"{i:03d}.csv" for i in range(1, 10)]


def test_all_weights_zero_falls_back_to_the_file_count():
    files = [f"{i:03d}.csv" for i in range(10)]
    assert split(files, 0.50, {p: 0 for p in files}) == split(files, 0.50)


def test_hold_out_takes_contiguous_blocks_spread_over_the_period():
    files = [f"{i:03d}.csv" for i in range(100)]
    kept, held = hold_out(files, 0.20, blocks=4)
    assert len(held) == 20 and len(kept) == 80
    runs = [held[0]]
    for a, b in zip(held, held[1:]):
        if int(b[:3]) != int(a[:3]) + 1:
            runs.append(b)
    assert len(runs) == 4, "each block has to be one unbroken stretch"
    assert int(runs[0][:3]) < 25 and int(runs[-1][:3]) > 70


def test_hold_out_drops_the_files_beside_each_block():
    files = [f"{i:03d}.csv" for i in range(100)]
    kept, held = hold_out(files, 0.10, blocks=2, gap=3)
    assert len(held) == 10
    assert len(kept) == 100 - 10 - 2 * 2 * 3
    assert not (set(kept) & set(held))
    for h in held:
        near = {f"{int(h[:3]) + d:03d}.csv" for d in (-1, 1)}
        assert not (near & set(kept)), "a kept file must not touch a held one"


def test_hold_out_without_a_gap_keeps_every_file():
    files = [f"{i:03d}.csv" for i in range(40)]
    kept, held = hold_out(files, 0.25, blocks=2)
    assert sorted(kept + held) == files


def test_moving_frames_counts_only_readings_above_the_gate(tmp_path):
    def ccvs1(kmh):
        raw = round(kmh / 0.00390625)
        return f"2020-11-23 08:00:00.000000;0x18FEF1E6;8;0;{raw & 0xFF};{(raw >> 8) & 0xFF};0;0;0;0;0"

    log = tmp_path / "a.csv"
    log.write_text("\n".join(["timestamp;id;dlc;data"]
                             + [ccvs1(kmh) for kmh in (0.0, 4.0, 6.0, 80.0)]
                             + ["2020-11-23 08:00:00.000000;0x18F004E6;8;0;0;0;0;0;0;0;0"]) + "\n")
    assert moving_frames([str(log)]) == {str(log): 2}
