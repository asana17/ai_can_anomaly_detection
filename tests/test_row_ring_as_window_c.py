import ctypes

import pytest

ROWS = 20    # WINDOW_MODEL_ROWS in board/lib/window_model/window_model_config.h
STRIDE = 10  # WINDOW_MODEL_STRIDE


@pytest.fixture(scope="module")
def c_window(board_lib):
    """Build board/lib/window_model/row_ring_as_window.h for this machine and give its functions.

    `push` adds the row numbered `no` with its `row_count_since_gap`, holding `no` in
    every signal.
    """
    library = board_lib(["window_model", "row_ring", "model"],
                        "#include <stddef.h>\n"
                        '#include "row_ring_as_window.h"\n'
                        "size_t window_size(void)\n"
                        "{\n\treturn sizeof(RowRingAsWindow);\n}\n"
                        "void clear(RowRingAsWindow *window)\n"
                        "{\n\trow_ring_as_window_clear(window);\n}\n"
                        "bool push(RowRingAsWindow *window, uint32_t no,"
                        " uint32_t row_count_since_gap)\n"
                        "{\n\tRowRingEntry entry = {.flag = false,"
                        " .row_count_since_gap = row_count_since_gap};\n\tuint32_t index;\n\n"
                        "\tfor (index = 0u; index < MODEL_SIGNALS; index++) {\n"
                        "\t\tentry.physical[index] = (float)no;\n\t}\n"
                        "\treturn row_ring_as_window_push(window, &entry);\n}\n"
                        "float oldest(const RowRingAsWindow *window)\n"
                        "{\n\treturn row_ring_as_window_entry(window, 0u)->physical[0];\n}\n"
                        "uint32_t held(const RowRingAsWindow *window)\n"
                        "{\n\treturn row_ring_as_window_count(window);\n}\n")
    library.window_size.restype = ctypes.c_size_t
    library.clear.argtypes = [ctypes.c_void_p]
    library.push.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]
    library.push.restype = ctypes.c_bool
    library.oldest.argtypes = [ctypes.c_void_p]
    library.oldest.restype = ctypes.c_float
    library.held.argtypes = [ctypes.c_void_p]
    library.held.restype = ctypes.c_uint32
    return library


@pytest.fixture
def window(c_window):
    """An empty window."""
    window = ctypes.create_string_buffer(c_window.window_size())
    c_window.clear(window)
    return window


def _ready(c_window, window, numbers, row_count_since_gap):
    """The row numbers a window ends at."""
    return [no for no, since in zip(numbers, row_count_since_gap) if c_window.push(window, no, since)]


def test_windows_come_at_rows_then_every_stride(c_window, window):
    numbers = range(1, 3 * ROWS + 1)
    assert _ready(c_window, window, numbers, range(len(numbers))) == list(
        range(ROWS, 3 * ROWS + 1, STRIDE))


def test_a_gap_empties_the_window(c_window, window):
    """A gap empties the window, and the first window after it waits ROWS rows."""
    before, after = range(1, ROWS), range(ROWS + 1, 2 * ROWS + 1)
    _ready(c_window, window, before, range(len(before)))
    assert _ready(c_window, window, after, range(len(after))) == [2 * ROWS]
    assert (c_window.held(window), c_window.oldest(window)) == (ROWS, ROWS + 1)


def test_rows_missed_in_a_run_keep_the_windows_in_place(c_window, window):
    """Rows the reader never saw empty the window, but windows still end where they would."""
    _ready(c_window, window, range(1, 13), range(0, 12))
    later = range(26, 3 * ROWS + 1)
    assert _ready(c_window, window, later, [no - 1 for no in later]) == [50, 60]
