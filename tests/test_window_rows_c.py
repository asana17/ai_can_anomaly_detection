import ctypes

import pytest

ROWS = 20    # WINDOW_MODEL_ROWS in board/lib/window_model/window_model_config.h
STRIDE = 10  # WINDOW_MODEL_STRIDE


@pytest.fixture(scope="module")
def c_rows(board_lib):
    """Build board/lib/window_model/window_rows.h for this machine and give its functions.

    `push` adds the row numbered `no` with its `row_count_since_gap`, holding `no` in
    every signal.
    """
    library = board_lib(["window_model", "row_ring", "model"],
                        "#include <stddef.h>\n"
                        '#include "window_rows.h"\n'
                        "size_t rows_size(void)\n"
                        "{\n\treturn sizeof(RowRing);\n}\n"
                        "void clear(RowRing *rows)\n"
                        "{\n\trow_ring_clear(rows);\n}\n"
                        "bool push(RowRing *rows, uint32_t no, uint32_t row_count_since_gap)\n"
                        "{\n\tRowRingEntry entry = {.flag = false,"
                        " .row_count_since_gap = row_count_since_gap};\n\tuint32_t i;\n\n"
                        "\tfor(i = 0u; i < MODEL_SIGNALS; i++) {\n"
                        "\t\tentry.physical[i] = (float)no;\n\t}\n"
                        "\treturn window_rows_push(rows, &entry);\n}\n"
                        "float oldest(const RowRing *rows)\n"
                        "{\n\treturn row_ring_entry(rows, 0u)->physical[0];\n}\n"
                        "uint32_t held(const RowRing *rows)\n"
                        "{\n\treturn row_ring_count(rows);\n}\n")
    library.rows_size.restype = ctypes.c_size_t
    library.clear.argtypes = [ctypes.c_void_p]
    library.push.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]
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


def _ready(c_rows, rows, numbers, row_count_since_gap):
    """The row numbers a window ends at."""
    return [no for no, since in zip(numbers, row_count_since_gap) if c_rows.push(rows, no, since)]


def test_windows_come_at_rows_then_every_stride(c_rows, rows):
    numbers = range(1, 3 * ROWS + 1)
    assert _ready(c_rows, rows, numbers, range(len(numbers))) == list(
        range(ROWS, 3 * ROWS + 1, STRIDE))


def test_a_gap_empties_the_rows(c_rows, rows):
    """A gap empties the rows, and the first window after it waits ROWS rows."""
    before, after = range(1, ROWS), range(ROWS + 1, 2 * ROWS + 1)
    _ready(c_rows, rows, before, range(len(before)))
    assert _ready(c_rows, rows, after, range(len(after))) == [2 * ROWS]
    assert (c_rows.held(rows), c_rows.oldest(rows)) == (ROWS, ROWS + 1)


def test_rows_missed_in_a_run_keep_the_windows_in_place(c_rows, rows):
    """Rows the reader never saw empty its rows, but windows still end where they would."""
    _ready(c_rows, rows, range(1, 13), range(0, 12))
    later = range(26, 3 * ROWS + 1)
    assert _ready(c_rows, rows, later, [no - 1 for no in later]) == [50, 60]
