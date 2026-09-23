from common import hub_dirs


def test_find_returns_the_newest_of_two_with_the_same_inputs(tmp_path, hub):
    hub.files = {"splits/20260101-000000/meta.json": {"inputs": {"hold": 1}},
                 "splits/20260102-000000/meta.json": {"inputs": {"hold": 1}}}
    found = hub_dirs.find("u/d", "splits", {"hold": 1}, str(tmp_path / "local"))
    assert found["path"] == "splits/20260102-000000"


def test_find_passes_over_a_directory_whose_meta_has_no_inputs(tmp_path, hub):
    hub.files = {"splits/20260101-000000/meta.json": {"inputs": {"hold": 1}},
                 "splits/20260102-000000/meta.json": {"made_from": "an old run"}}
    found = hub_dirs.find("u/d", "splits", {"hold": 1}, str(tmp_path / "local"))
    assert found["path"] == "splits/20260101-000000"


def test_a_dry_run_makes_nothing_and_names_a_new_one(tmp_path, hub):
    hub.files = {}
    made = []
    found = hub_dirs.reuse_or_make("u/d", "splits", {}, {"hold": 1}, str(tmp_path),
                                   made.append, dry_run=True)
    assert found == {"repo": "u/d", "revision": None, "path": "splits/<new>"}
    assert made == [] and hub.uploaded == []


def test_a_dry_run_still_finds_the_one_to_reuse(tmp_path, hub, capsys):
    hub.files = {"splits/20260101-000000/meta.json": {"inputs": {"hold": 1}}}
    found = hub_dirs.reuse_or_make("u/d", "splits", {}, {"hold": 1}, str(tmp_path),
                                   None, dry_run=True)
    assert found["path"] == "splits/20260101-000000"
    assert capsys.readouterr().out.split() == ["splits", "20260101-000000"]


def test_a_step_it_builds_lists_the_values_it_is_made_with(tmp_path, hub, capsys):
    hub.files = {}
    hub_dirs.reuse_or_make("u/d", "splits", {}, {"hold": 1}, str(tmp_path), None,
                           dry_run=True)
    assert capsys.readouterr().out.splitlines() == [
        f"{'splits':<24}<new>", f"  {'hold':<22}1"]


def test_a_step_it_builds_leaves_the_directories_it_reads_out(tmp_path, hub, capsys):
    hub.files = {}
    hub_dirs.reuse_or_make("u/d", "splits", {"grid": "grids/20260101-000000"},
                           {"hold": 1}, str(tmp_path), None, dry_run=True)
    assert "grids/20260101-000000" not in capsys.readouterr().out
