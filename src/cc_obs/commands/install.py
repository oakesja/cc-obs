import json
import sys

from cc_obs.project import find_project_root, settings_path

HOOK_EVENTS = [
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "Notification",
    "SubagentStart",
    "SubagentStop",
    "Stop",
    "SessionStart",
    "UserPromptSubmit",
    "PreCompact",
    "PermissionRequest",
    "TeammateIdle",
    "TaskCompleted",
]

CC_OBS_MARKER = "cc-obs"
CC_OBS_WRAP_PREFIX = "cc-obs wrap -- "


def _has_marker(entry: dict) -> bool:
    return any(CC_OBS_MARKER in h.get("command", "") for h in entry.get("hooks", []))


def _is_pure_cc_obs(entry: dict) -> bool:
    """True if every command in the entry is a cc-obs command (not just a wrapped one)."""
    for h in entry.get("hooks", []):
        cmd = h.get("command", "")
        if CC_OBS_MARKER in cmd and not cmd.startswith(CC_OBS_WRAP_PREFIX):
            return True
    return False


def _make_hooks() -> dict:
    hooks: dict[str, list] = {}

    for event in HOOK_EVENTS:
        if event == "SessionStart":
            hooks[event] = [
                {
                    "matcher": "startup",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "cc-obs clear --quiet && cc-obs log",
                        }
                    ],
                },
                {
                    "matcher": "resume|clear|compact",
                    "hooks": [{"type": "command", "command": "cc-obs log"}],
                },
            ]
        else:
            hooks[event] = [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "cc-obs log"}],
                },
            ]

    return hooks


def _wrap_entry(entry: dict) -> dict:
    """Wrap non-cc-obs command hooks with cc-obs wrap prefix."""
    wrapped = dict(entry)
    wrapped["hooks"] = []
    for h in entry.get("hooks", []):
        h = dict(h)
        if h.get("type") == "command":
            cmd = h["command"]
            if not cmd.startswith(CC_OBS_WRAP_PREFIX):
                h["command"] = CC_OBS_WRAP_PREFIX + cmd
        wrapped["hooks"].append(h)
    return wrapped


def _merge_hooks(existing: dict, new_hooks: dict) -> dict:
    """Merge new cc-obs hooks into existing settings, preserving non-cc-obs hooks."""
    result = dict(existing)
    existing_hooks = result.get("hooks", {})

    for event, new_entries in new_hooks.items():
        current = existing_hooks.get(event, [])
        kept = [_wrap_entry(e) for e in current if not _has_marker(e)]
        existing_hooks[event] = new_entries + kept

    result["hooks"] = existing_hooks
    return result


def _unwrap_entry(entry: dict) -> dict:
    """Remove cc-obs wrap prefix from command hooks."""
    unwrapped = dict(entry)
    unwrapped["hooks"] = []
    for h in entry.get("hooks", []):
        h = dict(h)
        if h.get("type") == "command":
            cmd = h["command"]
            if cmd.startswith(CC_OBS_WRAP_PREFIX):
                h["command"] = cmd[len(CC_OBS_WRAP_PREFIX) :]
        unwrapped["hooks"].append(h)
    return unwrapped


def _remove_hooks(existing: dict) -> dict:
    """Remove pure cc-obs hooks and unwrap cc-obs wrap prefixes."""
    result = dict(existing)
    hooks = result.get("hooks", {})

    for event in list(hooks.keys()):
        entries = hooks[event]
        kept = [_unwrap_entry(e) for e in entries if not _is_pure_cc_obs(e)]
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]

    if not hooks and "hooks" in result:
        del result["hooks"]

    return result


def run(project: bool = False, uninstall: bool = False) -> None:
    root = find_project_root()
    if root is None:
        print("No .claude directory found", file=sys.stderr)
        sys.exit(1)
        return

    path = settings_path(root, project=project)

    existing = {}
    if path.exists():
        existing = json.loads(path.read_text())

    if uninstall:
        updated = _remove_hooks(existing)
        action = "Uninstalled"
    else:
        new_hooks = _make_hooks()
        updated = _merge_hooks(existing, new_hooks)
        action = "Installed"

    path.write_text(json.dumps(updated, indent=2) + "\n")
    print(f"{action} cc-obs hooks in {path.relative_to(root)}")
