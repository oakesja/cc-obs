import json
from unittest.mock import patch

from cc_obs.commands.install_prompt import gather_choices, _discover_agents


class FakeQuestion:
    def __init__(self, answer):
        self._answer = answer

    def ask(self):
        return self._answer


AGENT_MD = """\
---
hooks:
  PostToolUse:
    - matcher: ""
      hooks:
        - type: command
          command: my-tool check
---
# Agent
"""


def test_gather_choices_project_selection(project_dir):
    answers = iter(
        [
            FakeQuestion(True),  # project selection
        ]
    )

    def fake_select(message, **kwargs):
        return next(answers)

    def fake_confirm(message, **kwargs):
        return FakeQuestion(True)

    def fake_text(message, **kwargs):
        return FakeQuestion("")

    def fake_checkbox(message, **kwargs):
        return FakeQuestion([])

    with (
        patch("cc_obs.commands.install_prompt.questionary.select", fake_select),
        patch("cc_obs.commands.install_prompt.questionary.confirm", fake_confirm),
        patch("cc_obs.commands.install_prompt.questionary.text", fake_text),
        patch("cc_obs.commands.install_prompt.questionary.checkbox", fake_checkbox),
    ):
        config = gather_choices(project_dir)

    assert config.project is True


def test_gather_choices_existing_hooks(project_dir):
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

    confirm_answers = iter([FakeQuestion(True), FakeQuestion(True)])
    text_answers = iter([FakeQuestion("My Tool")])

    def fake_select(message, **kwargs):
        return FakeQuestion(False)  # settings.local.json

    def fake_confirm(message, **kwargs):
        return next(confirm_answers)

    def fake_text(message, **kwargs):
        return next(text_answers)

    def fake_checkbox(message, **kwargs):
        return FakeQuestion([])

    with (
        patch("cc_obs.commands.install_prompt.questionary.select", fake_select),
        patch("cc_obs.commands.install_prompt.questionary.confirm", fake_confirm),
        patch("cc_obs.commands.install_prompt.questionary.text", fake_text),
        patch("cc_obs.commands.install_prompt.questionary.checkbox", fake_checkbox),
    ):
        config = gather_choices(project_dir)

    assert len(config.existing_hook_choices) == 1
    assert config.existing_hook_choices[0].command == "my-tool check"
    assert config.existing_hook_choices[0].wrap is True
    assert config.existing_hook_choices[0].name == "My Tool"


def test_discover_agents(project_dir):
    agent_file = project_dir / ".claude" / "agent.md"
    agent_file.write_text(AGENT_MD)

    no_hooks = project_dir / ".claude" / "readme.md"
    no_hooks.write_text("# Just a readme\n")

    agents = _discover_agents(project_dir)
    assert agent_file in agents
    assert no_hooks not in agents


def test_gather_choices_with_agents(project_dir):
    agent_file = project_dir / ".claude" / "agent.md"
    agent_file.write_text(AGENT_MD)

    text_answers = iter([FakeQuestion("Agent Hook")])

    def fake_select(message, **kwargs):
        return FakeQuestion(False)

    def fake_confirm(message, **kwargs):
        return FakeQuestion(True)

    def fake_text(message, **kwargs):
        return next(text_answers)

    def fake_checkbox(message, **kwargs):
        return FakeQuestion([agent_file])

    with (
        patch("cc_obs.commands.install_prompt.questionary.select", fake_select),
        patch("cc_obs.commands.install_prompt.questionary.confirm", fake_confirm),
        patch("cc_obs.commands.install_prompt.questionary.text", fake_text),
        patch("cc_obs.commands.install_prompt.questionary.checkbox", fake_checkbox),
    ):
        config = gather_choices(project_dir)

    assert len(config.agents) == 1
    assert config.agents[0].wrap is True
    assert config.agents[0].hook_names == {"my-tool check": "Agent Hook"}
