import json
import subprocess
import sys
import time
from datetime import datetime, timezone

from cc_obs.project import find_project_root, events_path, obs_dir


def run(cmd: list[str], name: str = "") -> None:
    if not cmd:
        print("Usage: cc-obs wrap -- <command>", file=sys.stderr)
        sys.exit(1)

    raw = sys.stdin.buffer.read()

    start = time.monotonic()
    result = subprocess.run(cmd, input=raw, capture_output=True)
    duration_ms = round((time.monotonic() - start) * 1000, 1)

    # Pass through stdout/stderr exactly
    sys.stdout.buffer.write(result.stdout)
    sys.stdout.buffer.flush()
    sys.stderr.buffer.write(result.stderr)
    sys.stderr.buffer.flush()

    # Log the wrapped event
    if raw:
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            event = {}

        cwd = event.get("cwd")
        root = find_project_root(cwd)
        if root is not None:
            out_dir = obs_dir(root)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = events_path(root)

            seq = 1
            if out_file.exists():
                with open(out_file, "rb") as f:
                    seq = sum(1 for _ in f) + 1

            event["_ts"] = datetime.now(timezone.utc).isoformat()
            event["_seq"] = seq
            wrap_data = {
                "command": " ".join(cmd),
                "exit_code": result.returncode,
                "duration_ms": duration_ms,
                "stdout": result.stdout.decode(errors="replace"),
                "stderr": result.stderr.decode(errors="replace"),
            }
            if name:
                wrap_data["name"] = name
            event["_wrap"] = wrap_data

            with open(out_file, "a") as f:
                f.write(json.dumps(event, separators=(",", ":")) + "\n")

    sys.exit(result.returncode)
