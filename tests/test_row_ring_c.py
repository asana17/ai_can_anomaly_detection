import ctypes

import pytest

ROWS = 20  # WINDOW_MODEL_ROWS in board/lib/window_model/window_model_config.h


@pytest.fixture(scope="module")
def c_ring(board_lib):
    """Build board/lib/row_ring for this machine and give its functions.

    A row pushed as `value` holds `value` in every signal, so a read shows it is whole.
    """
    library = board_lib(["row_ring", "window_model", "model"],
                        "#include <stddef.h>\n"
                        '#include "row_ring.h"\n'
                        "size_t ring_size(void)\n"
                        "{\n\treturn sizeof(RowRing);\n}\n"
                        "void clear(RowRing *ring)\n"
                        "{\n\trow_ring_clear(ring);\n}\n"
                        "void push(RowRing *ring, float value, bool flag)\n"
                        "{\n\tfloat physical[MODEL_SIGNALS];\n\tuint32_t i;\n\n"
                        "\tfor(i = 0u; i < MODEL_SIGNALS; i++) {\n"
                        "\t\tphysical[i] = value;\n\t}\n"
                        "\trow_ring_push(ring, physical, flag);\n}\n"
                        "uint32_t read(const RowRing *ring, float *values, uint8_t *flags)\n"
                        "{\n\tconst float *physical;\n\tuint32_t i;\n\n"
                        "\tfor(i = 0u; i < row_ring_count(ring); i++) {\n"
                        "\t\tphysical = row_ring_physical(ring, i);\n"
                        "\t\tvalues[i] = physical[0];\n"
                        "\t\tflags[i] = row_ring_flag(ring, i);\n"
                        "\t\tif(physical[MODEL_SIGNALS - 1u] != physical[0]) {\n"
                        "\t\t\treturn 0u;\n\t\t}\n\t}\n"
                        "\treturn row_ring_count(ring);\n}\n")
    library.ring_size.restype = ctypes.c_size_t
    library.clear.argtypes = [ctypes.c_void_p]
    library.push.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_bool]
    library.read.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float),
                             ctypes.POINTER(ctypes.c_uint8)]
    library.read.restype = ctypes.c_uint32
    return library


@pytest.fixture
def ring(c_ring):
    """An empty ring."""
    ring = ctypes.create_string_buffer(c_ring.ring_size())
    c_ring.clear(ring)
    return ring


def _read(c_ring, ring):
    """The rows the ring holds, as their values, and their flags, oldest first."""
    values = (ctypes.c_float * ROWS)()
    flags = (ctypes.c_uint8 * ROWS)()
    count = c_ring.read(ring, values, flags)
    return list(values)[:count], list(flags)[:count]


def test_a_ring_not_yet_full_holds_every_row(c_ring, ring):
    for value in range(5):
        c_ring.push(ring, value, value == 3)
    assert _read(c_ring, ring) == ([0, 1, 2, 3, 4], [0, 0, 0, 1, 0])


def test_a_full_ring_writes_over_the_oldest(c_ring, ring):
    for value in range(ROWS + 7):
        c_ring.push(ring, value, value % 2 == 0)
    values, flags = _read(c_ring, ring)
    assert values == list(range(7, ROWS + 7))
    assert flags == [int(value % 2 == 0) for value in range(7, ROWS + 7)]


def test_clear_empties_the_ring(c_ring, ring):
    for value in range(ROWS + 3):
        c_ring.push(ring, value, False)
    c_ring.clear(ring)
    c_ring.push(ring, 100, True)
    assert _read(c_ring, ring) == ([100], [1])
