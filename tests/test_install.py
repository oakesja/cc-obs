import json

import pytest

from cc_obs.commands.install import run


def test_install_creates_hooks(project_dir):
    run()
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

    run()

    data = json.loads(settings.read_text())
    commands = [
        h["command"]
        for entry in data["hooks"]["PostToolUse"]
        for h in entry.get("hooks", [])
    ]
    assert "cc-obs wrap -- my-tool" in commands
    assert any("cc-obs log" in c for c in commands)


def test_install_idempotent(project_dir):
    run()
    run()
    settings = project_dir / ".claude" / "settings.local.json"
    data = json.loads(settings.read_text())
    cc_obs_entries = [
        entry
        for entry in data["hooks"]["PostToolUse"]
        if any("cc-obs" in h.get("command", "") for h in entry.get("hooks", []))
    ]
    assert len(cc_obs_entries) == 1


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

    run(uninstall=True)

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

    run(uninstall=True)

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

    run()

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

    run()

    data = json.loads(settings.read_text())
    commands = [
        h["command"]
        for entry in data["hooks"]["PostToolUse"]
        for h in entry.get("hooks", [])
    ]
    assert "cc-obs wrap -- my-tool check" in commands
    # Original unwrapped command should not remain
    assert "my-tool check" not in commands


def test_uninstall_unwraps_existing_hooks(project_dir):
    """Uninstall should remove cc-obs log hooks AND unwrap cc-obs wrap prefixes."""
    settings = project_dir / ".claude" / "settings.local.json"
    # Simulate what install produces: cc-obs log first, then wrapped user hook
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

    run(uninstall=True)

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
    run(project=True)
    assert (project_dir / ".claude" / "settings.json").exists()
    assert not (project_dir / ".claude" / "settings.local.json").exists()
