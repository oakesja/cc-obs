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
    assert "my-tool" in commands
    assert any("cc-obs" in c for c in commands)


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


def test_no_project_root_exits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run()
    assert exc.value.code == 1


def test_project_flag(project_dir):
    run(project=True)
    assert (project_dir / ".claude" / "settings.json").exists()
    assert not (project_dir / ".claude" / "settings.local.json").exists()
