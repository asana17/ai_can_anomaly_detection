from assemble.split import moving_frames, split


def test_split_fraction_sizes():
    files = [f"{i:03d}.csv" for i in range(100)]
    train, val, test = split(files, 0.70, 0.05)
    assert (len(train), len(val), len(test)) == (70, 5, 25)


def test_orders_by_filename_before_splitting():
    files = ["c.csv", "a.csv", "b.csv"]  # not in order
    train, val, test = split(files, 0.34, 0.33)
    assert train + val + test == ["a.csv", "b.csv", "c.csv"]


def test_partitions_cover_all_without_overlap():
    files = [f"{i:04d}.csv" for i in range(50)]
    train, val, test = split(files, 0.70, 0.05)
    assert train + val + test == sorted(files)
    assert not (set(train) & set(val)) and not (set(val) & set(test))


def test_a_weight_sizes_the_blocks_instead_of_the_file_count():
    files = [f"{i:03d}.csv" for i in range(10)]
    weight = {p: (100 if i < 2 else 0) for i, p in enumerate(files)}
    weight["009.csv"] = 100                       # the only moving traffic late on
    train, val, test = split(files, 0.34, 0.33, weight)
    assert train == ["000.csv"]                   # a third of the moving traffic
    assert val == [f"{i:03d}.csv" for i in range(1, 9)]
    assert test == ["009.csv"]


def test_a_log_with_no_weight_does_not_consume_a_share():
    files = [f"{i:03d}.csv" for i in range(6)]
    weight = {p: (0 if i < 3 else 10) for i, p in enumerate(files)}
    train, val, test = split(files, 0.50, 0.25, weight)
    assert train == ["000.csv", "001.csv", "002.csv", "003.csv"]
    assert val == ["004.csv"] and test == ["005.csv"]


def test_all_weights_zero_falls_back_to_the_file_count():
    files = [f"{i:03d}.csv" for i in range(10)]
    weighted = split(files, 0.50, 0.20, {p: 0 for p in files})
    assert weighted == split(files, 0.50, 0.20)
    assert [len(block) for block in weighted] == [5, 2, 3]


def test_moving_frames_counts_only_readings_above_the_gate(tmp_path):
    def ccvs1(kmh):
        raw = round(kmh / 0.00390625)
        return f"2020-11-23 08:00:00.000000;0x18FEF1E6;8;0;{raw & 0xFF};{(raw >> 8) & 0xFF};0;0;0;0;0"

    log = tmp_path / "a.csv"
    log.write_text("\n".join(["timestamp;id;dlc;data"]
                             + [ccvs1(kmh) for kmh in (0.0, 4.0, 6.0, 80.0)]
                             + ["2020-11-23 08:00:00.000000;0x18F004E6;8;0;0;0;0;0;0;0;0"]) + "\n")
    assert moving_frames([str(log)]) == {str(log): 2}
