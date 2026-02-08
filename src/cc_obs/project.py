from pathlib import Path


def find_project_root(cwd: str | None = None) -> Path | None:
    """Walk up from cwd looking for a .claude directory."""
    start = Path(cwd) if cwd else Path.cwd()
    for parent in [start, *start.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return None


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
