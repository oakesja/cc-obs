import pytest

from cc_obs.commands.view import run


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
