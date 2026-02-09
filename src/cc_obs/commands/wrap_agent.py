import copy
from pathlib import Path

import yaml

CC_OBS_PREFIX = "cc-obs wrap "


def wrap_file(path: Path, hook_names: dict[str, str] | None = None) -> None:
    text = path.read_text()
    frontmatter, body = _split_frontmatter(text)
    if "hooks" not in frontmatter:
        return
    frontmatter = _wrap_hooks(frontmatter, hook_names or {})
    path.write_text(_join_frontmatter(frontmatter, body))


def unwrap_file(path: Path) -> None:
    text = path.read_text()
    frontmatter, body = _split_frontmatter(text)
    if "hooks" not in frontmatter:
        return
    if not _has_cc_obs(frontmatter):
        return
    frontmatter = _unwrap_hooks(frontmatter)
    path.write_text(_join_frontmatter(frontmatter, body))


def _has_cc_obs(frontmatter: dict) -> bool:
    for entries in frontmatter.get("hooks", {}).values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                if hook.get("type") == "command" and hook.get("command", "").startswith(
                    CC_OBS_PREFIX
                ):
                    return True
    return False


def _split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text

    end = text.index("\n---", 3)
    yaml_text = text[3:end].strip()
    body = text[end + 4 :]
    if body.startswith("\n"):
        body = body[1:]

    return yaml.safe_load(yaml_text) or {}, body


def _join_frontmatter(frontmatter: dict, body: str) -> str:
    yaml_text = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_text}---\n{body}"


def _wrap_hooks(frontmatter: dict, hook_names: dict[str, str] | None = None) -> dict:
    result = copy.deepcopy(frontmatter)
    names = hook_names or {}
    for entries in result["hooks"].values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                if hook.get("type") == "command":
                    cmd = hook["command"]
                    if not cmd.startswith(CC_OBS_PREFIX):
                        name = names.get(cmd, "")
                        if name:
                            hook["command"] = f'cc-obs wrap --name "{name}" -- {cmd}'
                        else:
                            hook["command"] = f"cc-obs wrap -- {cmd}"
    return result


def _unwrap_hooks(frontmatter: dict) -> dict:
    result = copy.deepcopy(frontmatter)
    for entries in result["hooks"].values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                if hook.get("type") == "command":
                    cmd = hook["command"]
                    if cmd.startswith(CC_OBS_PREFIX):
                        dash_idx = cmd.find("-- ", len(CC_OBS_PREFIX))
                        if dash_idx != -1:
                            hook["command"] = cmd[dash_idx + 3 :]
    return result
