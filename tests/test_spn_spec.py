from preprocess.frames.spn_decode import decode
from preprocess.frames.spn_spec import SPEC


def _find(pgn, name):
    return next(d for d in SPEC[pgn] if d.name == name)


def test_engine_speed_decodes():
    # EEC1 bytes 4-5 = 0x10, 0x27 -> 10000 * 0.125 = 1250 rpm
    data = bytes([0, 0, 0, 0x10, 0x27, 0, 0, 0])
    assert decode(data, _find(61444, "engine_speed").field) == 1250.0


def test_wheel_speed_decodes():
    # CCVS1 bytes 2-3 = 0x00, 0x64 -> 0x6400 * 0.00390625 = 100 km/h
    data = bytes([0, 0x00, 0x64, 0, 0, 0, 0, 0])
    assert decode(data, _find(65265, "wheel_speed").field) == 100.0


def test_ranges_and_geometry_are_valid():
    for defs in SPEC.values():
        for d in defs:
            assert d.minimum < d.maximum
            assert d.field.length > 0
