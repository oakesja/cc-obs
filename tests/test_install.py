import json

import pytest

from cc_obs.commands.install import (
    AgentChoice,
    HookWrapChoice,
    InstallConfig,
    execute_install,
    run,
)


AGENT_MD = """\
---
hooks:
  PostToolUse:
    - matcher: ""
      hooks:
        - type: command
          command: my-tool check
---
# My Agent
"""


def test_install_creates_hooks(project_dir):
    execute_install(project_dir, InstallConfig())
    settings = project_dir / ".claude" / "settings.local.json"
    data = json.loads(settings.read_text())
    assert "hooks" in data
    assert "PostToolUse" in data["hooks"]
    assert any(
        "cc-obs" in h.get("command", "")
        for entry in data["hooks"]["PostToolUse"]
        for h in entry.get("hooks", [])
    )


def test_install_preserves_existing(project_dir):
    settings = project_dir / ".claude" / "settings.local.json"
    existing = {
        "hooks": {
            "PostToolUse": [
                {"matcher": "", "hooks": [{"type": "command", "command": "my-tool"}]}
            ]
        }
    }
    settings.write_text(json.dumps(existing))

    execute_install(project_dir, InstallConfig())

    data = json.loads(settings.read_text())
    commands = [
        h["command"]
        for entry in data["hooks"]["PostToolUse"]
        for h in entry.get("hooks", [])
    ]
    assert "cc-obs wrap -- my-tool" in commands
    assert any("cc-obs log" in c for c in commands)


def test_install_idempotent(project_dir):
    execute_install(project_dir, InstallConfig())
    execute_install(project_dir, InstallConfig())
    settings = project_dir / ".claude" / "settings.local.json"
    data = json.loads(settings.read_text())
    cc_obs_entries = [
        entry
        for entry in data["hooks"]["PostToolUse"]
        if any("cc-obs" in h.get("command", "") for h in entry.get("hooks", []))
    ]
    assert len(cc_obs_entries) == 1


def test_reinstall_preserves_wrapped_hooks(project_dir):
    settings = project_dir / ".claude" / "settings.local.json"
    existing = {
        "hooks": {
            "PostToolUse": [
                {"matcher": "", "hooks": [{"type": "command", "command": "my-tool"}]}
            ]
        }
    }
    settings.write_text(json.dumps(existing))

    execute_install(project_dir, InstallConfig())
    execute_install(project_dir, InstallConfig())

    data = json.loads(settings.read_text())
    commands = [
        h["command"]
        for entry in data["hooks"]["PostToolUse"]
        for h in entry.get("hooks", [])
    ]
    assert "cc-obs wrap -- my-tool" in commands
    assert any("cc-obs log" in c for c in commands)


def test_uninstall_removes_hooks(project_dir):
    settings = project_dir / ".claude" / "settings.local.json"
    existing = {
        "hooks": {
            "PostToolUse": [
                {"matcher": "", "hooks": [{"type": "command", "command": "my-tool"}]},
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "cc-obs log"}],
                },
            ]
        }
    }
    settings.write_text(json.dumps(existing))

    execute_install(project_dir, InstallConfig(uninstall=True))

    data = json.loads(settings.read_text())
    commands = [
        h["command"]
        for entry in data["hooks"].get("PostToolUse", [])
        for h in entry.get("hooks", [])
    ]
    assert "my-tool" in commands
    assert not any("cc-obs" in c for c in commands)


def test_uninstall_empty(project_dir):
    settings = project_dir / ".claude" / "settings.local.json"
    settings.write_text("{}")

    execute_install(project_dir, InstallConfig(uninstall=True))

    data = json.loads(settings.read_text())
    assert "hooks" not in data


def test_install_cc_obs_hooks_come_first(project_dir):
    settings = project_dir / ".claude" / "settings.local.json"
    existing = {
        "hooks": {
            "PostToolUse": [
                {"matcher": "", "hooks": [{"type": "command", "command": "my-tool"}]}
            ]
        }
    }
    settings.write_text(json.dumps(existing))

    execute_install(project_dir, InstallConfig())

    data = json.loads(settings.read_text())
    entries = data["hooks"]["PostToolUse"]
    first_commands = [h["command"] for h in entries[0].get("hooks", [])]
    assert any("cc-obs log" in c for c in first_commands)


def test_install_wraps_existing_hooks(project_dir):
    settings = project_dir / ".claude" / "settings.local.json"
    existing = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "my-tool check"}],
                }
            ]
        }
    }
    settings.write_text(json.dumps(existing))

    execute_install(project_dir, InstallConfig())

    data = json.loads(settings.read_text())
    commands = [
        h["command"]
        for entry in data["hooks"]["PostToolUse"]
        for h in entry.get("hooks", [])
    ]
    assert "cc-obs wrap -- my-tool check" in commands
    assert "my-tool check" not in commands


def test_uninstall_unwraps_existing_hooks(project_dir):
    settings = project_dir / ".claude" / "settings.local.json"
    existing = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "cc-obs log"}],
                },
                {
                    "matcher": "",
                    "hooks": [
                        {"type": "command", "command": "cc-obs wrap -- my-tool check"}
                    ],
                },
            ]
        }
    }
    settings.write_text(json.dumps(existing))

    execute_install(project_dir, InstallConfig(uninstall=True))

    data = json.loads(settings.read_text())
    commands = [
        h["command"]
        for entry in data["hooks"].get("PostToolUse", [])
        for h in entry.get("hooks", [])
    ]
    assert "my-tool check" in commands
    assert "cc-obs wrap -- my-tool check" not in commands
    assert "cc-obs log" not in commands


def test_no_project_root_exits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run()
    assert exc.value.code == 1


def test_project_flag(project_dir):
    execute_install(project_dir, InstallConfig(project=True))
    assert (project_dir / ".claude" / "settings.json").exists()
    assert not (project_dir / ".claude" / "settings.local.json").exists()


def test_execute_skips_wrap_when_choice_false(project_dir):
    settings = project_dir / ".claude" / "settings.local.json"
    existing = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "my-tool check"}],
                }
            ]
        }
    }
    settings.write_text(json.dumps(existing))

    config = InstallConfig(
        existing_hook_choices=[
            HookWrapChoice(event="PostToolUse", command="my-tool check", wrap=False)
        ]
    )
    execute_install(project_dir, config)

    data = json.loads(settings.read_text())
    commands = [
        h["command"]
        for entry in data["hooks"]["PostToolUse"]
        for h in entry.get("hooks", [])
    ]
    assert "my-tool check" in commands
    assert "cc-obs wrap -- my-tool check" not in commands


def test_execute_wrap_with_name(project_dir):
    settings = project_dir / ".claude" / "settings.local.json"
    existing = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "my-tool check"}],
                }
            ]
        }
    }
    settings.write_text(json.dumps(existing))

    config = InstallConfig(
        existing_hook_choices=[
            HookWrapChoice(
                event="PostToolUse", command="my-tool check", wrap=True, name="My Tool"
            )
        ]
    )
    execute_install(project_dir, config)

    data = json.loads(settings.read_text())
    commands = [
        h["command"]
        for entry in data["hooks"]["PostToolUse"]
        for h in entry.get("hooks", [])
    ]
    assert 'cc-obs wrap --name "My Tool" -- my-tool check' in commands


def test_execute_default_config_matches_current_behavior(project_dir):
    settings = project_dir / ".claude" / "settings.local.json"
    existing = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "my-tool"}],
                }
            ]
        }
    }
    settings.write_text(json.dumps(existing))

    execute_install(project_dir, InstallConfig())

    data = json.loads(settings.read_text())
    commands = [
        h["command"]
        for entry in data["hooks"]["PostToolUse"]
        for h in entry.get("hooks", [])
    ]
    assert "cc-obs wrap -- my-tool" in commands
    assert any("cc-obs log" in c for c in commands)


def test_execute_wraps_agent(project_dir):
    agent_file = project_dir / ".claude" / "agent.md"
    agent_file.write_text(AGENT_MD)

    config = InstallConfig(agents=[AgentChoice(path=agent_file, wrap=True)])
    execute_install(project_dir, config)

    content = agent_file.read_text()
    assert "cc-obs wrap -- my-tool check" in content


def test_execute_skips_agent_when_not_selected(project_dir):
    agent_file = project_dir / ".claude" / "agent.md"
    agent_file.write_text(AGENT_MD)

    config = InstallConfig(agents=[AgentChoice(path=agent_file, wrap=False)])
    execute_install(project_dir, config)

    content = agent_file.read_text()
    assert "cc-obs wrap" not in content


def test_uninstall_unwraps_agents(project_dir):
    agent_file = project_dir / ".claude" / "agent.md"
    agent_file.write_text(
        AGENT_MD.replace("my-tool check", "cc-obs wrap -- my-tool check")
    )

    execute_install(project_dir, InstallConfig(uninstall=True))

    content = agent_file.read_text()
    assert "cc-obs wrap" not in content
    assert "my-tool check" in content


def test_uninstall_unwraps_named_hooks(project_dir):
    settings = project_dir / ".claude" / "settings.local.json"
    existing = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "cc-obs log"}],
                },
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'cc-obs wrap --name "My Tool" -- my-tool check',
                        }
                    ],
                },
            ]
        }
    }
    settings.write_text(json.dumps(existing))

    execute_install(project_dir, InstallConfig(uninstall=True))

    data = json.loads(settings.read_text())
    commands = [
        h["command"]
        for entry in data["hooks"].get("PostToolUse", [])
        for h in entry.get("hooks", [])
    ]
    assert "my-tool check" in commands
    assert not any("cc-obs" in c for c in commands)
