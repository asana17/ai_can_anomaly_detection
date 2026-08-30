from datetime import datetime, timezone

from preprocess.frames.can_log_loader import load_can_log

_SAMPLE = (
    "timestamp;id;dlc;data\n"
    "2020-11-23 08:03:31.985194;0x10ff80e6;8;0;0;251;109;240;144;255;255\n"
    "2020-11-23 08:03:31.988986;0x1cff80e6;1;230\n"
)


def _write(tmp_path, text):
    path = tmp_path / "log.csv"
    path.write_text(text)
    return path


def test_parses_fields_and_skips_header(tmp_path):
    frames = list(load_can_log(_write(tmp_path, _SAMPLE)))
    assert len(frames) == 2
    assert frames[0].can_id == 0x10FF80E6
    assert frames[0].data == bytes([0, 0, 251, 109, 240, 144, 255, 255])


def test_dlc_controls_data_length(tmp_path):
    frames = list(load_can_log(_write(tmp_path, _SAMPLE)))
    assert len(frames[0].data) == 8
    assert frames[1].data == bytes([230])


def test_timestamp_is_epoch_seconds(tmp_path):
    frames = list(load_can_log(_write(tmp_path, _SAMPLE)))
    expected = datetime(
        2020, 11, 23, 8, 3, 31, 985194, tzinfo=timezone.utc
    ).timestamp()
    assert frames[0].timestamp == expected


def test_blank_lines_are_ignored(tmp_path):
    frames = list(load_can_log(_write(tmp_path, _SAMPLE + "\n")))
    assert len(frames) == 2


def test_timestamp_without_fraction(tmp_path):
    # some rows are logged to whole seconds, with no ".ffffff"
    path = _write(
        tmp_path,
        "timestamp;id;dlc;data\n2020-11-23 08:23:08;0x18f004e6;1;0\n",
    )
    expected = datetime(2020, 11, 23, 8, 23, 8, tzinfo=timezone.utc).timestamp()
    assert list(load_can_log(path))[0].timestamp == expected
