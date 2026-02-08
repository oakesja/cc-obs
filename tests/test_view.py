import json
import tempfile
from pathlib import Path

import pytest

from cc_obs.commands.view import run
from cc_obs.viewer import render_html


def test_view_generates_html(project_dir, events_file, write_events, monkeypatch):
    write_events(
        [
            {
                "session_id": "s1",
                "hook_event_name": "Stop",
                "_ts": "2025-01-01T00:00:00Z",
                "_seq": 1,
            },
        ]
    )
    monkeypatch.setattr("webbrowser.open", lambda url: None)
    run()
    vp = project_dir / ".claude" / "cc-obs" / "view.html"
    assert vp.exists()
    assert "<html" in vp.read_text().lower()


def test_view_no_open(project_dir, events_file, write_events, monkeypatch):
    write_events(
        [
            {
                "session_id": "s1",
                "hook_event_name": "Stop",
                "_ts": "2025-01-01T00:00:00Z",
                "_seq": 1,
            },
        ]
    )
    opened = []
    monkeypatch.setattr("webbrowser.open", lambda url: opened.append(url))
    run(no_open=True)
    assert len(opened) == 0


def test_view_no_events_file(project_dir, capsys):
    run()
    assert "No events logged yet" in capsys.readouterr().out


def test_view_no_project_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run()
    assert exc.value.code == 1


def test_view_log_file(tmp_path, monkeypatch):
    log_file = tmp_path / "test.jsonl"
    events = [
        {
            "session_id": "s1",
            "hook_event_name": "SessionStart",
            "_ts": "2025-01-01T00:00:00Z",
            "_seq": 1,
        },
        {
            "session_id": "s1",
            "hook_event_name": "Stop",
            "_ts": "2025-01-01T00:01:00Z",
            "_seq": 2,
        },
    ]
    log_file.write_text("\n".join(json.dumps(e) for e in events) + "\n")

    monkeypatch.setattr("webbrowser.open", lambda url: None)
    run(log_file=str(log_file))

    vp = Path(tempfile.gettempdir()) / "cc-obs-view.html"
    assert vp.exists()
    html = vp.read_text()
    assert "<html" in html.lower()
    assert "s1" in html


def test_view_log_file_not_found(tmp_path, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        run(log_file=str(tmp_path / "missing.jsonl"))
    assert exc.value.code == 1


def test_view_log_file_empty(tmp_path, capsys, monkeypatch):
    log_file = tmp_path / "empty.jsonl"
    log_file.write_text("")
    run(log_file=str(log_file))
    assert "No events in file" in capsys.readouterr().out


def test_view_html_has_tabs():
    events = [
        {
            "session_id": "s1",
            "hook_event_name": "SessionStart",
            "_ts": "2025-01-01T00:00:00Z",
            "_seq": 1,
        },
    ]
    html = render_html(events)
    assert "tab-btn" in html
    assert "Timeline" in html
    assert "Agent Tree" in html
    assert "Spans" in html
    assert "switchTab" in html


def test_view_html_has_spans_view():
    events = [
        {
            "session_id": "s1",
            "hook_event_name": "SessionStart",
            "_ts": "2025-01-01T00:00:00Z",
            "_seq": 1,
        },
    ]
    html = render_html(events)
    assert "view-spans" in html
    assert "renderSpans" in html
    assert "spans-container" in html


def test_view_html_has_view_containers():
    events = [
        {
            "session_id": "s1",
            "hook_event_name": "Stop",
            "_ts": "2025-01-01T00:00:00Z",
            "_seq": 1,
        },
    ]
    html = render_html(events)
    assert "view-timeline" in html
    assert "view-agent-tree" in html
    assert "view-spans" in html
    assert 'class="view-container active"' in html


def test_view_log_file_with_sample_fixture(monkeypatch):
    fixture = Path(__file__).parent / "fixtures" / "sample_session.jsonl"
    assert fixture.exists(), "Sample fixture should exist"

    monkeypatch.setattr("webbrowser.open", lambda url: None)
    run(log_file=str(fixture))

    vp = Path(tempfile.gettempdir()) / "cc-obs-view.html"
    assert vp.exists()
    html = vp.read_text()
    assert "sample-abc-123" in html
    assert "Grep" in html
    assert "SubagentStart" in html
