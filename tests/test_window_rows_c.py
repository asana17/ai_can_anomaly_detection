import ctypes

import pytest

ROWS = 20    # WINDOW_MODEL_ROWS in board/lib/window_model/window_model_config.h
STRIDE = 10  # WINDOW_MODEL_STRIDE


@pytest.fixture(scope="module")
def c_rows(board_lib):
    """Build board/lib/window_model/window_rows.h for this machine and give its functions.

    `push` adds the row numbered `no`, holding `no` in every signal.
    """
    library = board_lib(["window_model", "row_ring", "model"],
                        "#include <stddef.h>\n"
                        '#include "window_rows.h"\n'
                        "size_t rows_size(void)\n"
                        "{\n\treturn sizeof(WindowRows);\n}\n"
                        "void clear(WindowRows *rows)\n"
                        "{\n\twindow_rows_clear(rows);\n}\n"
                        "bool push(WindowRows *rows, uint32_t no)\n"
                        "{\n\tfloat physical[MODEL_SIGNALS];\n\tuint32_t i;\n\n"
                        "\tfor(i = 0u; i < MODEL_SIGNALS; i++) {\n"
                        "\t\tphysical[i] = (float)no;\n\t}\n"
                        "\twindow_rows_restart_on_gap(rows, no);\n"
                        "\treturn window_rows_push(rows, physical, false);\n}\n"
                        "float oldest(const WindowRows *rows)\n"
                        "{\n\treturn row_ring_physical(&rows->ring, 0u)[0];\n}\n"
                        "uint32_t held(const WindowRows *rows)\n"
                        "{\n\treturn row_ring_count(&rows->ring);\n}\n")
    library.rows_size.restype = ctypes.c_size_t
    library.clear.argtypes = [ctypes.c_void_p]
    library.push.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    library.push.restype = ctypes.c_bool
    library.oldest.argtypes = [ctypes.c_void_p]
    library.oldest.restype = ctypes.c_float
    library.held.argtypes = [ctypes.c_void_p]
    library.held.restype = ctypes.c_uint32
    return library


@pytest.fixture
def rows(c_rows):
    """Empty rows."""
    rows = ctypes.create_string_buffer(c_rows.rows_size())
    c_rows.clear(rows)
    return rows


def test_windows_come_at_rows_then_every_stride(c_rows, rows):
    ready = [no for no in range(1, 3 * ROWS + 1) if c_rows.push(rows, no)]
    assert ready == list(range(ROWS, 3 * ROWS + 1, STRIDE))


def test_a_gap_empties_the_rows(c_rows, rows):
    """After a gap the rows before it are gone and the first window waits ROWS rows."""
    for no in range(1, ROWS):
        c_rows.push(rows, no)
    after = range(ROWS + 1, 2 * ROWS + 1)
    ready = [no for no in after if c_rows.push(rows, no)]
    assert ready == [2 * ROWS]
    assert (c_rows.held(rows), c_rows.oldest(rows)) == (ROWS, ROWS + 1)
