import pytest

from common.schema_validate import check


def test_a_nan_is_refused_though_the_schema_takes_any_number():
    with pytest.raises(ValueError):
        check([{"model": "pca", "k": 2, "losses": [float("nan")]}], "losses.schema.json")
