from preprocess.frames.frame_decode import decode_frame


def test_decodes_named_signals():
    # EEC1 (61444): engine speed bytes 4-5 = 0x10, 0x27 -> 1250 rpm
    data = bytes([0, 0, 0, 0x10, 0x27, 0, 0, 0])
    values = decode_frame(61444, data)
    assert values["engine_speed"] == 1250.0
    assert values["driver_demand_torque"] == -125.0  # byte 0 -> 0 + offset -125


def test_na_fields_are_omitted():
    # LFE1 (65266): only fuel_rate carries data, the rest is 0xFF
    values = decode_frame(65266, bytes([54, 0, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]))
    assert values == {"fuel_rate": 2.7}


def test_unknown_pgn_returns_empty():
    assert decode_frame(65408, bytes(8)) == {}
