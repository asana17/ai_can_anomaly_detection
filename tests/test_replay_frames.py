from datetime import datetime, timezone

import pytest

from board.replay_frames import header, kept, log_at, started
from preprocess.frames.can_log_loader import CanFrame

EEC1 = 0x0CF004E6  # PGN 61444, which the board decodes
OTHER = 0x18FEEEE6  # PGN 65262, which it does not


def test_a_log_starts_when_its_name_says():
    assert started("data/part_3/20210204093604325088.csv") == datetime(
        2021, 2, 4, 9, 36, 4, 325088, tzinfo=timezone.utc).timestamp()


def test_the_log_at_a_time_is_the_last_to_start_before_it():
    paths = ["a/20210204093604000000.csv", "a/20210204093704000000.csv",
             "a/20210204093804000000.csv"]
    at = datetime(2021, 2, 4, 9, 37, 30, tzinfo=timezone.utc).timestamp()
    assert log_at(paths, at) == "a/20210204093704000000.csv"


def test_no_log_before_a_time_is_an_error():
    with pytest.raises(ValueError):
        log_at(["a/20210204093604000000.csv"], 0.0)


def test_only_the_decoded_pgns_in_the_span_are_kept():
    frames = [CanFrame(1.0, EEC1, b"\1"), CanFrame(2.0, OTHER, b"\2"),
              CanFrame(2.5, EEC1, b"\3"), CanFrame(4.0, EEC1, b"\4")]
    assert kept(frames, 1.0, 3.0) == [frames[0], frames[2]]


def test_the_header_gives_times_from_the_first_frame_and_pads_the_payload():
    text = header([CanFrame(10.0, EEC1, b"\x01\x02"), CanFrame(10.25, EEC1, b"")],
                  "a/20210204093604000000.csv", 5, 6)
    assert "#define REPLAY_FRAMES 2" in text
    assert "{0u, 0x0cf004e6u, 2u, {0x01, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}}," in text
    assert "{250000u, 0x0cf004e6u, 0u, {0x00" in text
