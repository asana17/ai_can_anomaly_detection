from attack.spn_encode import encode, set_field
from preprocess.frames.spn_decode import decode
from preprocess.frames.spn_spec import SPEC


def _field(pgn, name):
    return next(d for d in SPEC[pgn] if d.name == name).field


def test_round_trip_engine_speed():
    field = _field(61444, "engine_speed")
    assert decode(set_field(bytes(8), field, 1250.0), field) == 1250.0


def test_round_trip_with_offset():
    field = _field(61444, "driver_demand_torque")  # offset -125
    assert decode(set_field(bytes(8), field, -50.0), field) == -50.0


def test_set_field_leaves_other_bits_untouched():
    field = _field(65265, "wheel_speed")  # bytes 1-2
    data = bytes([0x11, 0, 0, 0x44, 0x55, 0x66, 0x77, 0x88])
    out = set_field(data, field, 100.0)
    assert out[0] == 0x11 and out[3:] == data[3:]
    assert decode(out, field) == 100.0
