import json
import sys
import webbrowser

from cc_obs.project import find_project_root, events_path, view_path
from cc_obs.viewer import render_html


def run(no_open: bool = False) -> None:
    root = find_project_root()
    if root is None:
        print("No .claude directory found", file=sys.stderr)
        sys.exit(1)
        return

    ep = events_path(root)
    if not ep.exists():
        print("No events logged yet")
        return

    events = []
    with open(ep) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))

    if not events:
        print("No events logged yet")
        return

    vp = view_path(root)
    vp.write_text(render_html(events))
    print(f"Generated {vp.relative_to(root)}")

    if not no_open:
        webbrowser.open(vp.as_uri())
