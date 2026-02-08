import json

from cc_obs.commands.log import run


def test_log_creates_event(project_dir, sample_event, events_file, feed_stdin):
    feed_stdin(json.dumps(sample_event).encode())
    run()
    assert events_file.exists()
    event = json.loads(events_file.read_text().strip())
    assert "_ts" in event
    assert event["_seq"] == 1
    assert event["session_id"] == "test-session-123"


def test_log_increments_seq(project_dir, sample_event, events_file, feed_stdin):
    feed_stdin(json.dumps(sample_event).encode())
    run()

    feed_stdin(json.dumps(sample_event).encode())
    run()

    lines = events_file.read_text().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["_seq"] == 1
    assert json.loads(lines[1])["_seq"] == 2


def test_log_empty_stdin(project_dir, events_file, feed_stdin):
    feed_stdin(b"")
    run()
    assert not events_file.exists()


def test_log_invalid_json(project_dir, events_file, feed_stdin):
    feed_stdin(b"not json")
    run()
    assert not events_file.exists()


def test_log_no_project_root(tmp_path, monkeypatch, feed_stdin):
    monkeypatch.chdir(tmp_path)
    event = {"session_id": "x", "hook_event_name": "Stop", "cwd": str(tmp_path)}
    feed_stdin(json.dumps(event).encode())
    run()
    # No crash, no file created
    assert not (tmp_path / ".claude" / "cc-obs" / "events.jsonl").exists()


def test_log_enriches_subagent_stop(project_dir, events_file, feed_stdin):
    # Create a fake transcript with tool_use entries
    transcript = project_dir / "transcript.jsonl"
    transcript_entries = [
        {
            "message": {
                "content": [
                    {"type": "tool_use", "id": "tool-1", "name": "Bash"},
                    {"type": "tool_use", "id": "tool-2", "name": "Read"},
                ]
            }
        }
    ]
    transcript.write_text("\n".join(json.dumps(e) for e in transcript_entries) + "\n")

    # Log prior tool_use events that match transcript IDs
    prior_events = [
        {
            "session_id": "s1",
            "hook_event_name": "PostToolUse",
            "tool_use_id": "tool-1",
            "cwd": str(project_dir),
        },
        {
            "session_id": "s1",
            "hook_event_name": "PostToolUse",
            "tool_use_id": "tool-2",
            "cwd": str(project_dir),
        },
    ]
    for ev in prior_events:
        feed_stdin(json.dumps(ev).encode())
        run()

    # Now log SubagentStop
    stop_event = {
        "session_id": "s1",
        "hook_event_name": "SubagentStop",
        "agent_id": "agent-abc",
        "agent_type": "task",
        "agent_transcript_path": str(transcript),
        "cwd": str(project_dir),
    }
    feed_stdin(json.dumps(stop_event).encode())
    run()

    # Check that prior events got enriched
    lines = events_file.read_text().strip().splitlines()
    for line in lines[:2]:
        ev = json.loads(line)
        assert ev["_agent_id"] == "agent-abc"
        assert ev["_agent_type"] == "task"
