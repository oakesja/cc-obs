import json
import sys

import pytest

from cc_obs.commands.wrap import run


def test_wrap_runs_command(project_dir, sample_event, events_file, feed_stdin):
    feed_stdin(json.dumps(sample_event).encode())
    with pytest.raises(SystemExit) as exc:
        run(["echo", "hello"])
    assert exc.value.code == 0
    assert events_file.exists()
    event = json.loads(events_file.read_text().strip())
    assert "_wrap" in event
    assert event["_wrap"]["exit_code"] == 0
    assert "hello" in event["_wrap"]["stdout"]
    assert "duration_ms" in event["_wrap"]


def test_wrap_captures_stderr(project_dir, sample_event, events_file, feed_stdin):
    feed_stdin(json.dumps(sample_event).encode())
    with pytest.raises(SystemExit) as exc:
        run([sys.executable, "-c", "import sys; sys.stderr.write('oops\\n')"])
    assert exc.value.code == 0
    event = json.loads(events_file.read_text().strip())
    assert "oops" in event["_wrap"]["stderr"]


def test_wrap_propagates_exit_code(project_dir, sample_event, events_file, feed_stdin):
    feed_stdin(json.dumps(sample_event).encode())
    with pytest.raises(SystemExit) as exc:
        run([sys.executable, "-c", "raise SystemExit(42)"])
    assert exc.value.code == 42


def test_wrap_no_command_exits():
    with pytest.raises(SystemExit) as exc:
        run([])
    assert exc.value.code == 1


def test_wrap_name_in_event(project_dir, sample_event, events_file, feed_stdin):
    feed_stdin(json.dumps(sample_event).encode())
    with pytest.raises(SystemExit) as exc:
        run(["echo", "hello"], name="my label")
    assert exc.value.code == 0
    event = json.loads(events_file.read_text().strip())
    assert event["_wrap"]["name"] == "my label"


def test_wrap_name_omitted_when_empty(
    project_dir, sample_event, events_file, feed_stdin
):
    feed_stdin(json.dumps(sample_event).encode())
    with pytest.raises(SystemExit) as exc:
        run(["echo", "hello"])
    assert exc.value.code == 0
    event = json.loads(events_file.read_text().strip())
    assert "name" not in event["_wrap"]


def test_wrap_empty_stdin(project_dir, events_file, feed_stdin):
    feed_stdin(b"")
    with pytest.raises(SystemExit) as exc:
        run(["echo", "hello"])
    assert exc.value.code == 0
    # No event logged when stdin is empty
    assert not events_file.exists()
