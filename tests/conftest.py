import io
import json

import pytest


@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    """Create a minimal project structure and chdir into it."""
    (tmp_path / ".claude" / "cc-obs").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def events_file(project_dir):
    """Return the events.jsonl path (doesn't create the file)."""
    return project_dir / ".claude" / "cc-obs" / "events.jsonl"


@pytest.fixture
def sample_event(project_dir):
    """Return a minimal valid hook event dict."""
    return {
        "session_id": "test-session-123",
        "hook_event_name": "PostToolUse",
        "cwd": str(project_dir),
    }


@pytest.fixture
def feed_stdin(monkeypatch):
    """Return a helper that monkeypatches sys.stdin with a BytesIO-backed object."""

    def _feed(data: bytes):
        buf = io.BytesIO(data)
        wrapper = io.TextIOWrapper(buf)
        monkeypatch.setattr("sys.stdin", wrapper)

    return _feed


@pytest.fixture
def write_events(events_file):
    """Write a list of event dicts to events.jsonl."""

    def _write(events: list[dict]):
        lines = [json.dumps(e, separators=(",", ":")) for e in events]
        events_file.write_text("\n".join(lines) + "\n")

    return _write
