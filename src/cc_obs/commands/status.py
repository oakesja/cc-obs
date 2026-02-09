import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from cc_obs.project import events_path


def run() -> None:
    root = Path.cwd()
    if not (root / ".claude").is_dir():
        print("No .claude directory found", file=sys.stderr)
        sys.exit(1)

    path = events_path(root)
    if not path.exists():
        print("No events logged yet")
        return

    events = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))

    if not events:
        print("No events logged yet")
        return

    session_id = events[0].get("session_id", "unknown")
    model = events[0].get("model", "unknown")

    event_counts = Counter(e.get("hook_event_name", "unknown") for e in events)
    tool_counts = Counter(e["tool_name"] for e in events if "tool_name" in e)

    timestamps = [e["_ts"] for e in events if "_ts" in e]
    first = timestamps[0] if timestamps else None
    last = timestamps[-1] if timestamps else None

    file_size = path.stat().st_size
    if file_size < 1024:
        size_str = f"{file_size} B"
    elif file_size < 1024 * 1024:
        size_str = f"{file_size / 1024:.1f} KB"
    else:
        size_str = f"{file_size / (1024 * 1024):.1f} MB"

    duration_str = ""
    if first and last:
        t0 = datetime.fromisoformat(first)
        t1 = datetime.fromisoformat(last)
        secs = (t1 - t0).total_seconds()
        if secs < 60:
            duration_str = f"{secs:.1f}s"
        elif secs < 3600:
            duration_str = f"{secs / 60:.1f}m"
        else:
            duration_str = f"{secs / 3600:.1f}h"

    print(f"Session: {session_id}")
    print(f"Model:   {model}")
    print(f"Events:  {len(events)} ({size_str})")
    if duration_str:
        print(f"Span:    {duration_str} ({first} → {last})")

    print()
    print("Events by type:")
    for name, count in event_counts.most_common():
        print(f"  {name}: {count}")

    if tool_counts:
        print()
        print("Tool usage:")
        for name, count in tool_counts.most_common():
            print(f"  {name}: {count}")

    wrap_events = [e for e in events if "_wrap" in e]
    if wrap_events:
        total_ms = sum(e["_wrap"]["duration_ms"] for e in wrap_events)
        print()
        print(f"Wrapped hooks: {len(wrap_events)} ({total_ms:.0f}ms total)")
