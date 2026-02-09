import json
import sys
import tempfile
import webbrowser
from pathlib import Path

from cc_obs.project import events_path, view_path
from cc_obs.viewer import render_html


def run(no_open: bool = False, log_file: str | None = None) -> None:
    if log_file:
        lf = Path(log_file)
        if not lf.exists():
            print(f"File not found: {log_file}", file=sys.stderr)
            sys.exit(1)
            return
        events = _read_events(lf)
        if not events:
            print("No events in file")
            return
        vp = Path(tempfile.gettempdir()) / "cc-obs-view.html"
        vp.write_text(render_html(events))
        print(f"Generated {vp}")
    else:
        root = Path.cwd()
        if not (root / ".claude").is_dir():
            print("No .claude directory found", file=sys.stderr)
            sys.exit(1)
        ep = events_path(root)
        if not ep.exists():
            print("No events logged yet")
            return
        events = _read_events(ep)
        if not events:
            print("No events logged yet")
            return
        vp = view_path(root)
        vp.write_text(render_html(events))
        print(f"Generated {vp.relative_to(root)}")

    if not no_open:
        webbrowser.open(vp.as_uri())


def _read_events(path: Path) -> list[dict]:
    events = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events
