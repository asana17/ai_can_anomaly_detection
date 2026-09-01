from assemble.split import split


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
