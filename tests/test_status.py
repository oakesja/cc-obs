import pytest

from cc_obs.commands.status import run


def test_status_prints_summary(project_dir, write_events, capsys):
    write_events(
        [
            {
                "session_id": "sess-1",
                "model": "claude-opus-4-6",
                "hook_event_name": "PostToolUse",
                "_ts": "2025-01-01T00:00:00Z",
                "_seq": 1,
            },
            {
                "session_id": "sess-1",
                "model": "claude-opus-4-6",
                "hook_event_name": "Stop",
                "_ts": "2025-01-01T00:01:00Z",
                "_seq": 2,
            },
        ]
    )
    run()
    out = capsys.readouterr().out
    assert "sess-1" in out
    assert "claude-opus-4-6" in out
    assert "2" in out  # event count
    assert "PostToolUse" in out
    assert "Stop" in out


def test_status_with_tool_events(project_dir, write_events, capsys):
    write_events(
        [
            {
                "session_id": "s1",
                "model": "m",
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "_ts": "2025-01-01T00:00:00Z",
                "_seq": 1,
            },
            {
                "session_id": "s1",
                "model": "m",
                "hook_event_name": "PostToolUse",
                "tool_name": "Read",
                "_ts": "2025-01-01T00:00:01Z",
                "_seq": 2,
            },
        ]
    )
    run()
    out = capsys.readouterr().out
    assert "Tool usage" in out
    assert "Bash" in out
    assert "Read" in out


def test_status_with_wrap_events(project_dir, write_events, capsys):
    write_events(
        [
            {
                "session_id": "s1",
                "model": "m",
                "hook_event_name": "PostToolUse",
                "_ts": "2025-01-01T00:00:00Z",
                "_seq": 1,
                "_wrap": {
                    "command": "echo hi",
                    "exit_code": 0,
                    "duration_ms": 50.0,
                    "stdout": "hi\n",
                    "stderr": "",
                },
            },
        ]
    )
    run()
    out = capsys.readouterr().out
    assert "Wrapped hooks" in out


def test_status_no_events(project_dir, capsys):
    run()
    assert "No events logged yet" in capsys.readouterr().out


def test_status_no_project_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run()
    assert exc.value.code == 1
