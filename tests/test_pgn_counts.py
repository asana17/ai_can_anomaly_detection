from collections import Counter

from preprocess.frames.can_log_loader import CanFrame, load_can_log
from preprocess.profile.pgn_counts import count_pgn_senders, count_pgns


def _frame(can_id):
    return CanFrame(timestamp=0.0, can_id=can_id, data=b"")


def test_count_pgns():
    # 0x18F004E6 and 0x18F004E7 are PGN 61444; 0x10FF80E6 is PGN 65408
    counts = count_pgns([_frame(0x18F004E6), _frame(0x18F004E7), _frame(0x10FF80E6)])
    assert counts == Counter({61444: 2, 65408: 1})


def test_count_pgn_senders():
    # SA 230, 231, 230 on PGN 61444
    senders = count_pgn_senders(
        [_frame(0x18F004E6), _frame(0x18F004E7), _frame(0x18F004E6)]
    )
    assert senders[61444] == Counter({230: 2, 231: 1})


def test_counts_from_a_file(tmp_path):
    path = tmp_path / "log.csv"
    path.write_text(
        "timestamp;id;dlc;data\n"
        "2020-11-23 08:03:31.985194;0x18f004e6;1;0\n"
        "2020-11-23 08:03:31.986000;0x10ff80e6;1;0\n"
    )
    assert count_pgns(load_can_log(path)) == Counter({61444: 1, 65408: 1})
