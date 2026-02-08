import copy
import sys

import yaml

CC_OBS_PREFIX = "cc-obs wrap -- "


def run(agent_file: str, uninstall: bool = False) -> None:
    try:
        text = open(agent_file).read()
    except FileNotFoundError:
        print(f"File not found: {agent_file}", file=sys.stderr)
        sys.exit(1)

    frontmatter, body = _split_frontmatter(text)

    if "hooks" not in frontmatter:
        print(f"No hooks found in {agent_file}", file=sys.stderr)
        sys.exit(1)

    if uninstall:
        frontmatter = _unwrap_hooks(frontmatter)
        action = "Unwrapped"
    else:
        frontmatter = _wrap_hooks(frontmatter)
        action = "Wrapped"

    with open(agent_file, "w") as f:
        f.write(_join_frontmatter(frontmatter, body))

    print(f"{action} hooks in {agent_file}")


def _split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text

    end = text.index("---", 3)
    yaml_text = text[3:end].strip()
    body = text[end + 3 :]
    if body.startswith("\n"):
        body = body[1:]

    return yaml.safe_load(yaml_text) or {}, body


def _join_frontmatter(frontmatter: dict, body: str) -> str:
    yaml_text = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_text}---\n{body}"


def _wrap_hooks(frontmatter: dict) -> dict:
    result = copy.deepcopy(frontmatter)
    for entries in result["hooks"].values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                if hook.get("type") == "command":
                    cmd = hook["command"]
                    if not cmd.startswith(CC_OBS_PREFIX):
                        hook["command"] = CC_OBS_PREFIX + cmd
    return result


def _unwrap_hooks(frontmatter: dict) -> dict:
    result = copy.deepcopy(frontmatter)
    for entries in result["hooks"].values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                if hook.get("type") == "command":
                    cmd = hook["command"]
                    if cmd.startswith(CC_OBS_PREFIX):
                        hook["command"] = cmd[len(CC_OBS_PREFIX) :]
    return result
