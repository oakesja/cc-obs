import json
import sys
from datetime import datetime, timezone

from cc_obs.project import find_project_root, events_path, obs_dir


def run() -> None:
    raw = sys.stdin.buffer.read()
    if not raw:
        return

    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        return

    cwd = event.get("cwd")
    root = find_project_root(cwd)
    if root is None:
        return

    out_dir = obs_dir(root)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = events_path(root)

    seq = 1
    if out_file.exists():
        with open(out_file, "rb") as f:
            seq = sum(1 for _ in f) + 1

    event["_ts"] = datetime.now(timezone.utc).isoformat()
    event["_seq"] = seq

    with open(out_file, "a") as f:
        f.write(json.dumps(event, separators=(",", ":")) + "\n")
