import random

import pyarrow.parquet as pq

from assemble.test_set import inject_frames
from assemble.injected_frames import write_and_pass_frames
from test_test_set import MAX_HOLD, PERIOD, _rows_before_attack, _write_log


def test_the_frames_pass_on_unchanged_and_are_written(tmp_path):
    logs = [_write_log(tmp_path / f"{n}.csv") for n in "ab"]
    kw = dict(rows_before_attack=_rows_before_attack(logs), period=PERIOD,
              max_hold=MAX_HOLD, min_speed=5.0)
    injected = inject_frames(logs, random.Random(0), **kw)
    passed = list(write_and_pass_frames(injected, str(tmp_path / "f"), str(tmp_path), 1))
    expected = list(inject_frames(logs, random.Random(0), **kw))
    assert [item[:3] for item in passed] == [item[:3] for item in expected]

    table = pq.read_table(str(tmp_path / "f")).to_pydict()
    assert len(table["log"]) == sum(len(item[2]) for item in expected)
    assert set(table["log"]) == {"a.csv", "b.csv"}
    changed = sum(a.data != b.data for _, frames, hurt, _, _ in expected
                  for a, b in zip(frames, hurt))
    assert sum(table["attacked"]) == changed > 0
