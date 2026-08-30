from preprocess.frames.spn_decode import SpnField, decode, extract_le


def test_extract_le_16bit():
    # EEC1 engine speed: 16 bits at bit 24 (bytes 3-4), little-endian 0x2710
    data = bytes([0, 0, 0, 0x10, 0x27, 0, 0, 0])
    assert extract_le(data, 24, 16) == 10000


def test_extract_le_sub_byte():
    # byte 0 = 0b1011_0000; 2 bits at bit 4 -> 0b11
    assert extract_le(bytes([0b10110000]), 4, 2) == 3


def test_decode_applies_scale_and_offset():
    # engine speed 10000 * 0.125 rpm/bit = 1250.0
    data = bytes([0, 0, 0, 0x10, 0x27, 0, 0, 0])
    field = SpnField(start_bit=24, length=16, scale=0.125, offset=0.0)
    assert decode(data, field) == 1250.0


def test_decode_offset():
    # 8-bit with offset -125 (torque style); raw 125 -> 0.0
    field = SpnField(start_bit=0, length=8, scale=1.0, offset=-125.0)
    assert decode(bytes([125]), field) == 0.0


def test_all_ones_is_not_available():
    field = SpnField(start_bit=0, length=16, scale=1.0, offset=0.0)
    assert decode(bytes([0xFF, 0xFF]), field) is None
