import json
from pathlib import Path

import questionary
import yaml

from cc_obs.commands.install import (
    AgentChoice,
    HookWrapChoice,
    InstallConfig,
    CC_OBS_MARKER,
)
from cc_obs.commands.wrap_agent import _split_frontmatter
from cc_obs.project import settings_path


def gather_choices(root: Path) -> InstallConfig:
    project = questionary.select(
        "Where should cc-obs write hooks?",
        choices=[
            questionary.Choice("settings.local.json (gitignored)", value=False),
            questionary.Choice("settings.json (shared)", value=True),
        ],
    ).ask()

    if project is None:
        raise SystemExit(1)

    path = settings_path(root, project=project)
    existing = {}
    if path.exists():
        existing = json.loads(path.read_text())

    hook_choices = _ask_existing_hooks(existing)
    agents = _ask_agents(root)

    return InstallConfig(
        project=project,
        existing_hook_choices=hook_choices,
        agents=agents,
    )


def _ask_existing_hooks(settings: dict) -> list[HookWrapChoice]:
    choices = []
    hooks = settings.get("hooks", {})

    for event, entries in hooks.items():
        for entry in entries:
            for h in entry.get("hooks", []):
                cmd = h.get("command", "")
                if h.get("type") != "command" or CC_OBS_MARKER in cmd:
                    continue

                wrap = questionary.confirm(
                    f"Wrap existing hook? [{event}] {cmd}", default=True
                ).ask()
                if wrap is None:
                    raise SystemExit(1)

                name = ""
                if wrap:
                    name = (
                        questionary.text(
                            f"  Display name for '{cmd}' (enter to skip):"
                        ).ask()
                        or ""
                    )
                    if name is None:
                        raise SystemExit(1)

                choices.append(
                    HookWrapChoice(event=event, command=cmd, wrap=wrap, name=name)
                )

    return choices


def _discover_agents(root: Path) -> list[Path]:
    agents = []
    claude_dir = root / ".claude"
    for md in claude_dir.rglob("*.md"):
        if md.parent.name == "cc-obs":
            continue
        try:
            text = md.read_text()
            frontmatter, _ = _split_frontmatter(text)
        except (OSError, ValueError, yaml.YAMLError):
            continue
        if frontmatter.get("hooks"):
            agents.append(md)
    return agents


def _ask_agents(root: Path) -> list[AgentChoice]:
    agent_paths = _discover_agents(root)
    if not agent_paths:
        return []

    selected = questionary.checkbox(
        "Which agents should cc-obs wrap?",
        choices=[
            questionary.Choice(str(p.relative_to(root)), value=p) for p in agent_paths
        ],
    ).ask()

    if selected is None:
        raise SystemExit(1)

    selected_set = set(selected)
    results = []
    for p in agent_paths:
        if p not in selected_set:
            results.append(AgentChoice(path=p, wrap=False))
            continue

        text = p.read_text()
        frontmatter, _ = _split_frontmatter(text)
        hook_names: dict[str, str] = {}

        for entries in frontmatter.get("hooks", {}).values():
            for entry in entries:
                for h in entry.get("hooks", []):
                    cmd = h.get("command", "")
                    if h.get("type") == "command" and CC_OBS_MARKER not in cmd:
                        name = (
                            questionary.text(
                                f"  Display name for '{cmd}' in {p.name} (enter to skip):"
                            ).ask()
                            or ""
                        )
                        if name:
                            hook_names[cmd] = name

        results.append(AgentChoice(path=p, wrap=True, hook_names=hook_names))

    return results
