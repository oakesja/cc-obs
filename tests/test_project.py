from cc_obs.project import (
    find_project_root,
    obs_dir,
    events_path,
    view_path,
    settings_path,
)


def test_find_project_root(project_dir):
    assert find_project_root() == project_dir


def test_find_project_root_nested(project_dir):
    nested = project_dir / "a" / "b" / "c"
    nested.mkdir(parents=True)
    assert find_project_root(str(nested)) == project_dir


def test_find_project_root_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert find_project_root() is None


def test_path_helpers(project_dir):
    assert obs_dir(project_dir) == project_dir / ".claude" / "cc-obs"
    assert (
        events_path(project_dir) == project_dir / ".claude" / "cc-obs" / "events.jsonl"
    )
    assert view_path(project_dir) == project_dir / ".claude" / "cc-obs" / "view.html"
    assert settings_path(project_dir) == project_dir / ".claude" / "settings.local.json"
    assert (
        settings_path(project_dir, project=True)
        == project_dir / ".claude" / "settings.json"
    )
