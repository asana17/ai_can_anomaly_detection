from common import hub_dirs


def test_find_returns_the_newest_of_two_with_the_same_inputs(tmp_path, hub):
    hub.files = {"splits/20260101-000000/meta.json": {"inputs": {"hold": 1}},
                 "splits/20260102-000000/meta.json": {"inputs": {"hold": 1}}}
    found = hub_dirs.find("u/d", "splits", {"hold": 1}, str(tmp_path / "local"))
    assert found["path"] == "splits/20260102-000000"
