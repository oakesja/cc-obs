import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

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
CC_OBS_WRAP_PREFIX = "cc-obs wrap "


@dataclass
class HookWrapChoice:
    event: str
    command: str
    wrap: bool
    name: str = ""


@dataclass
class AgentChoice:
    path: Path
    wrap: bool
    hook_names: dict[str, str] = field(default_factory=dict)


@dataclass
class InstallConfig:
    project: bool = False
    uninstall: bool = False
    existing_hook_choices: list[HookWrapChoice] = field(default_factory=list)
    agents: list[AgentChoice] = field(default_factory=list)


def _is_already_wrapped(entry: dict) -> bool:
    return any(
        h.get("command", "").startswith(CC_OBS_WRAP_PREFIX)
        for h in entry.get("hooks", [])
        if h.get("type") == "command"
    )


def _is_pure_cc_obs(entry: dict) -> bool:
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


def _wrap_entry(entry: dict, name: str = "") -> dict:
    wrapped = dict(entry)
    wrapped["hooks"] = []
    for h in entry.get("hooks", []):
        h = dict(h)
        if h.get("type") == "command":
            cmd = h["command"]
            if not cmd.startswith(CC_OBS_WRAP_PREFIX):
                if name:
                    h["command"] = f'cc-obs wrap --name "{name}" -- {cmd}'
                else:
                    h["command"] = f"cc-obs wrap -- {cmd}"
        wrapped["hooks"].append(h)
    return wrapped


def _merge_hooks(
    existing: dict, new_hooks: dict, choices: list[HookWrapChoice] | None = None
) -> dict:
    result = dict(existing)
    existing_hooks = result.get("hooks", {})

    choices_by_key: dict[tuple[str, str], HookWrapChoice] = {}
    if choices:
        for c in choices:
            choices_by_key[(c.event, c.command)] = c

    for event, new_entries in new_hooks.items():
        current = existing_hooks.get(event, [])
        kept = []
        for e in current:
            if _is_pure_cc_obs(e):
                continue
            if _is_already_wrapped(e):
                kept.append(e)
                continue
            for h in e.get("hooks", []):
                cmd = h.get("command", "")
                choice = choices_by_key.get((event, cmd))
                if choice is not None and not choice.wrap:
                    kept.append(e)
                else:
                    name = choice.name if choice else ""
                    kept.append(_wrap_entry(e, name=name))
                break
            else:
                kept.append(e)
        existing_hooks[event] = new_entries + kept

    result["hooks"] = existing_hooks
    return result


def _unwrap_entry(entry: dict) -> dict:
    unwrapped = dict(entry)
    unwrapped["hooks"] = []
    for h in entry.get("hooks", []):
        h = dict(h)
        if h.get("type") == "command":
            cmd = h["command"]
            if cmd.startswith(CC_OBS_WRAP_PREFIX):
                # Strip everything up to and including "-- "
                dash_idx = cmd.find("-- ", len(CC_OBS_WRAP_PREFIX))
                if dash_idx != -1:
                    h["command"] = cmd[dash_idx + 3 :]
        unwrapped["hooks"].append(h)
    return unwrapped


def _remove_hooks(existing: dict) -> dict:
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


def execute_install(root: Path, config: InstallConfig) -> None:
    path = settings_path(root, project=config.project)

    existing = {}
    if path.exists():
        existing = json.loads(path.read_text())

    if config.uninstall:
        updated = _remove_hooks(existing)
        action = "Uninstalled"

        from cc_obs.commands.wrap_agent import unwrap_file

        for md in (root / ".claude").rglob("*.md"):
            unwrap_file(md)
    else:
        new_hooks = _make_hooks()
        updated = _merge_hooks(
            existing, new_hooks, choices=config.existing_hook_choices or None
        )
        action = "Installed"

        from cc_obs.commands.wrap_agent import wrap_file

        for agent in config.agents:
            if agent.wrap:
                wrap_file(agent.path, hook_names=agent.hook_names)

    path.write_text(json.dumps(updated, indent=2) + "\n")
    print(f"{action} cc-obs hooks in {path.relative_to(root)}")


def run(
    project: bool = False, uninstall: bool = False, no_prompt: bool = False
) -> None:
    root = find_project_root()
    if root is None:
        print("No .claude directory found", file=sys.stderr)
        sys.exit(1)
        return

    if not no_prompt and not uninstall and sys.stdin.isatty():
        from cc_obs.commands.install_prompt import gather_choices

        config = gather_choices(root)
    else:
        config = InstallConfig(project=project, uninstall=uninstall)

    execute_install(root, config)
