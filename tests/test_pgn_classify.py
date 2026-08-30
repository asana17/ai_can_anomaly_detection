from preprocess.profile.pgn_classify import is_proprietary_pgn


def test_proprietary_b_pf_255():
    assert is_proprietary_pgn(0xFF80)    # 65408
    assert is_proprietary_pgn(0x1FF55)   # 130901, data page 1


def test_proprietary_a_and_a2():
    assert is_proprietary_pgn(61184)     # 0xEF00
    assert is_proprietary_pgn(126720)    # 0x1EF00


def test_standard_pgns_are_not_proprietary():
    assert not is_proprietary_pgn(61444)  # EEC1
    assert not is_proprietary_pgn(65265)  # CCVS1
