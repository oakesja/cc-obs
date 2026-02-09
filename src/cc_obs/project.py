from pathlib import Path


def obs_dir(project_root: Path) -> Path:
    return project_root / ".claude" / "cc-obs"


def events_path(project_root: Path) -> Path:
    return obs_dir(project_root) / "events.jsonl"


def view_path(project_root: Path) -> Path:
    return obs_dir(project_root) / "view.html"


def settings_path(project_root: Path, project: bool = False) -> Path:
    if project:
        return project_root / ".claude" / "settings.json"
    return project_root / ".claude" / "settings.local.json"
