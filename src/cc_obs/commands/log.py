import json
import sys
from datetime import datetime, timezone
from pathlib import Path

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

    if event.get("hook_event_name") == "SubagentStop":
        _enrich_agent_tool_uses(out_file, event)


def _enrich_agent_tool_uses(events_file: Path, stop_event: dict) -> None:
    transcript_path = stop_event.get("agent_transcript_path")
    if not transcript_path:
        return

    transcript = Path(transcript_path)
    if not transcript.exists():
        return

    agent_id = stop_event.get("agent_id")
    agent_type = stop_event.get("agent_type")
    if not agent_id:
        return

    tool_use_ids = _extract_tool_use_ids(transcript)
    if not tool_use_ids:
        return

    lines = events_file.read_text().splitlines()
    updated = []
    changed = False
    for line in lines:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            updated.append(line)
            continue

        if ev.get("tool_use_id") in tool_use_ids:
            ev["_agent_id"] = agent_id
            ev["_agent_type"] = agent_type
            updated.append(json.dumps(ev, separators=(",", ":")))
            changed = True
        else:
            updated.append(line)

    if changed:
        events_file.write_text("\n".join(updated) + "\n")


def _extract_tool_use_ids(transcript: Path) -> set[str]:
    ids: set[str] = set()
    for line in transcript.read_text().splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = entry.get("message")
        if not message:
            continue
        for block in message.get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tool_id = block.get("id")
                if tool_id:
                    ids.add(tool_id)
    return ids
