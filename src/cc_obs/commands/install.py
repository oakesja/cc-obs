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


def _make_hooks() -> dict:
    hooks: dict[str, list] = {}

    for event in HOOK_EVENTS:
        if event == "SessionStart":
            hooks[event] = [
                {
                    "matcher": "startup",
                    "command": "cc-obs clear --quiet && cc-obs log",
                },
                {
                    "matcher": "resume|clear|compact",
                    "command": "cc-obs log",
                },
            ]
        else:
            hooks[event] = [
                {
                    "matcher": "",
                    "command": "cc-obs log",
                },
            ]

    return hooks


def _merge_hooks(existing: dict, new_hooks: dict) -> dict:
    """Merge new cc-obs hooks into existing settings, preserving non-cc-obs hooks."""
    result = dict(existing)
    existing_hooks = result.get("hooks", {})

    for event, new_entries in new_hooks.items():
        current = existing_hooks.get(event, [])
        # Keep entries that don't contain cc-obs
        kept = [e for e in current if CC_OBS_MARKER not in e.get("command", "")]
        existing_hooks[event] = kept + new_entries

    result["hooks"] = existing_hooks
    return result


def _remove_hooks(existing: dict) -> dict:
    """Remove all cc-obs hooks from settings."""
    result = dict(existing)
    hooks = result.get("hooks", {})

    for event in list(hooks.keys()):
        entries = hooks[event]
        kept = [e for e in entries if CC_OBS_MARKER not in e.get("command", "")]
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]

    if not hooks:
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
