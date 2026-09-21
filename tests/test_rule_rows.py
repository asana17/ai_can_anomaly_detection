import numpy as np

from board.rule_rows import bits, header, window


def test_the_attack_sits_in_the_middle():
    assert window(40, 49, 100, 20) == slice(35, 55)


def test_the_window_stays_in_the_rows():
    assert window(2, 3, 100, 20) == slice(0, 20)
    assert window(97, 98, 100, 20) == slice(80, 100)


def test_bits_are_the_float32_bits():
    assert bits(np.array([[1.0, -2.0, 0.1]], np.float32)) == [
        ["0x3f800000", "0xc0000000", "0x3dcccccd"]]


def test_the_bits_read_back_to_the_same_floats():
    rows = np.random.default_rng(0).standard_normal((3, 4)).astype(np.float32)
    back = np.array([[int(word, 16) for word in row] for row in bits(rows)], np.uint32)
    assert np.array_equal(back.view(np.float32), rows)


def test_the_header_declares_the_shape():
    text = header(np.zeros((3, 17), np.float32), 42)
    assert "#define RULE_ROWS 3" in text
    assert "#define RULE_SIGNALS 17" in text
    assert "#define FIRST_ROW 42" in text
    assert text.count("0x00000000") == 3 * 17
