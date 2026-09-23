import json

import pytest

from common.settings import Settings, read_settings


def test_no_file_gives_the_defaults():
    assert read_settings(None) == Settings()


def test_the_file_s_values_replace_the_defaults(tmp_path):
    (tmp_path / "s.json").write_text(json.dumps({"FOLD": 0, "HOLD": [1, 5]}))
    assert read_settings(str(tmp_path / "s.json")) == Settings(FOLD=0, HOLD=(1, 5))


def test_a_name_settings_does_not_have_raises(tmp_path):
    (tmp_path / "s.json").write_text(json.dumps({"FOLDS": 0}))
    with pytest.raises(TypeError):
        read_settings(str(tmp_path / "s.json"))
