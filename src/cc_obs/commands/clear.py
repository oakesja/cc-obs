import sys

from cc_obs.project import find_project_root, events_path, view_path


def run(quiet: bool = False) -> None:
    root = find_project_root()
    if root is None:
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
