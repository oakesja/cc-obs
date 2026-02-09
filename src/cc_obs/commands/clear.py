import sys
from pathlib import Path

from cc_obs.project import events_path, view_path


def run(quiet: bool = False) -> None:
    root = Path.cwd()
    if not (root / ".claude").is_dir():
        if not quiet:
            print("No .claude directory found", file=sys.stderr)
            sys.exit(1)
        return

    deleted = []
    for path in [events_path(root), view_path(root)]:
        if path.exists():
            path.unlink()
            deleted.append(path.name)

    if not quiet:
        if deleted:
            print(f"Cleared: {', '.join(deleted)}")
        else:
            print("Nothing to clear")
