import json

import pytest

from common.settings import RunSettings, SplitSettings, TestRunSettings, read_settings


def test_an_empty_file_gives_every_stage_its_defaults(tmp_path):
    (tmp_path / "s.json").write_text("{}")
    assert read_settings(str(tmp_path / "s.json")) == RunSettings()


def test_a_stage_s_values_replace_its_defaults_alone(tmp_path):
    (tmp_path / "s.json").write_text(json.dumps({"split_test_logs": {"FOLD": 0},
                                                 "run_test_set": {"HOLD": [1, 5]}}))
    each = read_settings(str(tmp_path / "s.json"))
    assert each.split_test_logs == SplitSettings(FOLD=0)
    assert each.run_test_set == TestRunSettings(HOLD=(1, 5))
    assert each.test_set == RunSettings().test_set


def test_a_stage_that_takes_no_settings_raises(tmp_path):
    (tmp_path / "s.json").write_text(json.dumps({"fit": {"SEED": 5}}))
    with pytest.raises(ValueError):
        read_settings(str(tmp_path / "s.json"))


def test_a_name_the_stage_does_not_have_raises(tmp_path):
    (tmp_path / "s.json").write_text(json.dumps({"train_set": {"FOLD": 0}}))
    with pytest.raises(TypeError):
        read_settings(str(tmp_path / "s.json"))
