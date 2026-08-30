from preprocess.frames.can_id_decompose import CanId, decompose_can_id


def test_eec1_broadcast_example_from_docs():
    # docs/can_data.md worked example: 0x18F004E6 -> EEC1
    assert decompose_can_id(0x18F004E6) == CanId(
        priority=6, pgn=61444, source_address=230
    )


def test_pdu2_folds_pdu_specific_into_pgn():
    # PF=0xFF (>=240, PDU2), PS=0x80 -> PGN 65408, the most frequent PGN in the data
    result = decompose_can_id(0x10FF80E6)
    assert result.pgn == 65408
    assert result.source_address == 230
    assert result.priority == 4


def test_pdu1_excludes_destination_from_pgn():
    # PF=0xEA (<240, PDU1), PS=0xFF is a destination address, not part of the PGN
    result = decompose_can_id(0x18EAFFFE)
    assert result.pgn == 59904  # Request
    assert result.source_address == 254
    assert result.priority == 6


def test_bits_above_29_are_masked():
    assert decompose_can_id(0xF8F004E6) == decompose_can_id(0x18F004E6)
