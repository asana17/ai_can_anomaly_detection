import ctypes

import numpy as np
import pytest

from preprocess.features.windows import positions, window_ends, window_rows

# W and S besides the ones in board/lib/window_model/window_model_config.h
OTHER_ROWS_AND_STRIDES = [(1, 1), (3, 1), (5, 2), (8, 3), (4, 4), (6, 9)]


@pytest.fixture(scope="module")
def c_window(board_lib):
    """Build board/lib/window_model/row_ring_as_window.h for this machine and give its functions.

    Called with W and S, it builds with those in place of the ones in window_model_config.h.
    `push` adds the row numbered `no`, holding `no` in every signal.
    """
    built = {}

    def build(rows=None, stride=None):
        if (rows, stride) in built:
            return built[rows, stride]
        # window_model_config.h has an include guard, so row_ring_as_window.h keeps these
        config = ""
        if rows is not None:
            config = ('#include "window_model_config.h"\n'
                      "#undef WINDOW_MODEL_ROWS\n#undef WINDOW_MODEL_STRIDE\n"
                      f"#define WINDOW_MODEL_ROWS {rows}u\n#define WINDOW_MODEL_STRIDE {stride}u\n")
        library = board_lib(["window_model", "model", "signals"],
                            "#include <stddef.h>\n" + config +
                            '#include "row_ring_as_window.h"\n'
                            "uint32_t rows(void)\n{\n\treturn WINDOW_MODEL_ROWS;\n}\n"
                            "uint32_t stride(void)\n{\n\treturn WINDOW_MODEL_STRIDE;\n}\n"
                            "size_t window_size(void)\n"
                            "{\n\treturn sizeof(RowRingAsWindow);\n}\n"
                            "void clear(RowRingAsWindow *window)\n"
                            "{\n\trow_ring_as_window_clear(window);\n}\n"
                            "bool push(RowRingAsWindow *window, uint32_t no, bool flag,"
                            " uint32_t row_count_since_gap)\n"
                            "{\n\tRowRingEntry entry = {.flag = flag,"
                            " .row_count_since_gap = row_count_since_gap};\n\tuint32_t index;\n\n"
                            "\tfor (index = 0u; index < SIGNAL_COUNT; index++) {\n"
                            "\t\tentry.physical[index] = (float)no;\n\t}\n"
                            "\trow_ring_as_window_push(window, &entry);\n"
                            "\treturn row_ring_as_window_is_complete(window);\n}\n"
                            "float entry_no(const RowRingAsWindow *window, uint32_t index)\n"
                            "{\n\treturn row_ring_as_window_entry(window, index)->physical[0];\n}\n")
        library.rows.restype = ctypes.c_uint32
        library.stride.restype = ctypes.c_uint32
        library.window_size.restype = ctypes.c_size_t
        library.clear.argtypes = [ctypes.c_void_p]
        library.push.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
        library.push.restype = ctypes.c_bool
        library.entry_no.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        library.entry_no.restype = ctypes.c_float
        built[rows, stride] = library
        return library
    return build


@pytest.fixture(params=[None, *OTHER_ROWS_AND_STRIDES],
                ids=["config", *(f"W{w}-S{s}" for w, s in OTHER_ROWS_AND_STRIDES)])
def library(request, c_window):
    """The C window, with the W and S of window_model_config.h and then with others."""
    if request.param is None:
        return c_window()
    return c_window(*request.param)


def _c_windows(library, moving, segment, flag):
    """The windows the board builds, as their row numbers, oldest first.

    Only moving rows reach the board. Each gets the row_count_since_gap the PC gives it.
    """
    window = ctypes.create_string_buffer(library.window_size())
    library.clear(window)
    windows = []
    for no, since in enumerate(positions(moving, segment)):
        if since >= 0 and library.push(window, no, bool(flag[no]), int(since)):
            windows.append([int(library.entry_no(window, i)) for i in range(library.rows())])
    return np.array(windows, int).reshape(-1, library.rows())


def _pc_windows(library, moving, segment):
    """The windows the PC builds, as their row numbers, oldest first."""
    rows = library.rows()
    ends = window_ends(positions(moving, segment), rows=rows, stride=library.stride())
    return window_rows(np.arange(len(moving)), ends, rows=rows)


def _hand_built(rows):
    """Rows with runs shorter than, as long as and longer than `rows`, ended by still rows
    or by a new segment, with flagged rows in them."""
    moving, segment, now = [], [], 0
    for length, still_after, new_segment_after in [
            (rows - 1, 1, False),      # shorter
            (rows, 1, False),          # as long as, right after a gap
            (3 * rows + 2, 2, False),  # longer
            (2 * rows, 0, True),       # ended by a new segment
            (rows, 0, True),           # as long as, right after the new segment
            (rows + 1, 1, False)]:
        moving += [True] * length + [False] * still_after
        segment += [now] * (length + still_after)
        now += new_segment_after
    moving = np.array(moving)
    return moving, np.array(segment), np.arange(len(moving)) % 3 == 0


def test_same_windows_on_hand_built_rows(library):
    moving, segment, flag = _hand_built(library.rows())
    np.testing.assert_array_equal(_c_windows(library, moving, segment, flag),
                                  _pc_windows(library, moving, segment))


def test_same_windows_on_random_rows(library):
    rng = np.random.default_rng(0)
    rows = library.rows()
    lengths = rng.integers(1, 3 * rows + 3, 400)
    moving = np.repeat(np.arange(len(lengths)) % 2 == 0, lengths)
    segment = np.cumsum(rng.random(len(moving)) < 0.01)
    flag = rng.random(len(moving)) < 0.1
    np.testing.assert_array_equal(_c_windows(library, moving, segment, flag),
                                  _pc_windows(library, moving, segment))
