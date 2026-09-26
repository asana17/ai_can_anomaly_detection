import ctypes

from preprocess.features.signal_state import SIGNALS


def test_the_header_numbers_each_signal_as_signals_does(board_lib):
    names = ", ".join(f"SIGNAL_{name.upper()}" for name in SIGNALS)
    library = board_lib(["signals"],
                        '#include "signals.h"\n'
                        f"static const int indices[] = {{{names}}};\n"
                        "int count(void)\n{\n\treturn SIGNAL_COUNT;\n}\n"
                        "int at(int k)\n{\n\treturn indices[k];\n}\n")
    library.at.argtypes = [ctypes.c_int]
    assert library.count() == len(SIGNALS)
    assert [library.at(k) for k in range(len(SIGNALS))] == list(range(len(SIGNALS)))
