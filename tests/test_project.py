from cc_obs.project import (
    obs_dir,
    events_path,
    view_path,
    settings_path,
)


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
