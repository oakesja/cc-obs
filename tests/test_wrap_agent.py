import pytest

from cc_obs.commands.wrap_agent import run


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

This is the agent body.
"""

AGENT_MD_WRAPPED = "cc-obs wrap -- my-tool check"


def test_wrap_agent_adds_prefix(tmp_path):
    f = tmp_path / "agent.md"
    f.write_text(AGENT_MD)
    run(str(f))
    content = f.read_text()
    assert AGENT_MD_WRAPPED in content


def test_wrap_agent_idempotent(tmp_path):
    f = tmp_path / "agent.md"
    f.write_text(AGENT_MD)
    run(str(f))
    run(str(f))
    content = f.read_text()
    # Should only have one prefix, not double
    assert content.count("cc-obs wrap -- cc-obs wrap --") == 0
    assert AGENT_MD_WRAPPED in content


def test_unwrap_agent_removes_prefix(tmp_path):
    f = tmp_path / "agent.md"
    f.write_text(AGENT_MD)
    run(str(f))
    assert AGENT_MD_WRAPPED in f.read_text()

    run(str(f), uninstall=True)
    content = f.read_text()
    assert "cc-obs wrap --" not in content
    assert "my-tool check" in content


def test_wrap_agent_file_not_found():
    with pytest.raises(SystemExit) as exc:
        run("/nonexistent/agent.md")
    assert exc.value.code == 1


def test_wrap_agent_no_hooks(tmp_path):
    f = tmp_path / "agent.md"
    f.write_text("---\ntitle: test\n---\nBody\n")
    with pytest.raises(SystemExit) as exc:
        run(str(f))
    assert exc.value.code == 1


def test_wrap_agent_preserves_body(tmp_path):
    f = tmp_path / "agent.md"
    f.write_text(AGENT_MD)
    run(str(f))
    content = f.read_text()
    assert "# My Agent" in content
    assert "This is the agent body." in content
