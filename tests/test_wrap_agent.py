import pytest

from cc_obs.commands.wrap_agent import wrap_file, unwrap_file, _split_frontmatter


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
    wrap_file(f)
    content = f.read_text()
    assert AGENT_MD_WRAPPED in content


def test_wrap_agent_idempotent(tmp_path):
    f = tmp_path / "agent.md"
    f.write_text(AGENT_MD)
    wrap_file(f)
    wrap_file(f)
    content = f.read_text()
    assert content.count("cc-obs wrap -- cc-obs wrap --") == 0
    assert AGENT_MD_WRAPPED in content


def test_unwrap_agent_removes_prefix(tmp_path):
    f = tmp_path / "agent.md"
    f.write_text(AGENT_MD)
    wrap_file(f)
    assert AGENT_MD_WRAPPED in f.read_text()

    unwrap_file(f)
    content = f.read_text()
    assert "cc-obs wrap" not in content
    assert "my-tool check" in content


def test_wrap_agent_no_hooks_is_noop(tmp_path):
    f = tmp_path / "agent.md"
    f.write_text("---\ntitle: test\n---\nBody\n")
    wrap_file(f)
    assert f.read_text() == "---\ntitle: test\n---\nBody\n"


def test_wrap_agent_preserves_body(tmp_path):
    f = tmp_path / "agent.md"
    f.write_text(AGENT_MD)
    wrap_file(f)
    content = f.read_text()
    assert "# My Agent" in content
    assert "This is the agent body." in content


def test_wrap_agent_with_names(tmp_path):
    f = tmp_path / "agent.md"
    f.write_text(AGENT_MD)
    wrap_file(f, hook_names={"my-tool check": "My Tool"})
    content = f.read_text()
    assert 'cc-obs wrap --name "My Tool" -- my-tool check' in content


def test_unwrap_agent_named_hooks(tmp_path):
    f = tmp_path / "agent.md"
    named = AGENT_MD.replace(
        "my-tool check", 'cc-obs wrap --name "My Tool" -- my-tool check'
    )
    f.write_text(named)
    unwrap_file(f)
    content = f.read_text()
    assert "cc-obs wrap" not in content
    assert "my-tool check" in content


def test_unwrap_noop_when_no_cc_obs(tmp_path):
    f = tmp_path / "agent.md"
    f.write_text(AGENT_MD)
    unwrap_file(f)
    assert f.read_text() == AGENT_MD


def test_split_frontmatter_dashes_in_yaml_value():
    text = "---\ntitle: some --- text\n---\nBody\n"
    frontmatter, body = _split_frontmatter(text)
    assert frontmatter == {"title": "some --- text"}
    assert body == "Body\n"


def test_split_frontmatter_no_closing_delimiter():
    text = "---\ntitle: test\nBody without closing delimiter\n"
    with pytest.raises(ValueError):
        _split_frontmatter(text)
