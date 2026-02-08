# cc-obs

Observability for Claude Code sessions. Installs lightweight hooks that log every lifecycle event (tool calls, agent activity, prompts, etc.) to JSONL, then lets you view a session as an interactive HTML dashboard.

## Install

```sh
uv tool install git+https://github.com/oakesja/cc-obs.git
```

## Setup

`cd` into any project that has a `.claude/` directory, then:

```sh
cc-obs install
```

This adds observer hooks to `.claude/settings.local.json` for all hook events. Hooks are silent — they append to a JSONL log without affecting Claude Code's behavior.

To write to the shared `settings.json` instead:

```sh
cc-obs install --project
```

To remove all hooks:

```sh
cc-obs install --uninstall
```

## Usage

Once installed, just use Claude Code normally. Events are logged automatically to `.claude/cc-obs/events.jsonl`. Logs are cleared at the start of each new session (but not on resume/compact).

## How it works

Claude Code [hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) fire shell commands at lifecycle events, passing a JSON payload on stdin. `cc-obs install` registers a `cc-obs log` hook for every event type. Each invocation reads the JSON, adds a timestamp (`_ts`) and sequence number (`_seq`), and appends it to the JSONL log.

The SessionStart hook has two matchers:
- `startup` — clears old logs then logs the event (fresh session)
- `resume|clear|compact` — logs without clearing (continuing a session)

## Log format

Each line in `events.jsonl` is the raw hook JSON plus `_ts` and `_seq`:

```jsonl
{"hook_event_name":"SessionStart","session_id":"abc","source":"startup","model":"claude-sonnet-4-5-20250929","_ts":"2025-01-01T00:00:00+00:00","_seq":1,...}
{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"npm test"},"_ts":"2025-01-01T00:00:01+00:00","_seq":2,...}
```

Wrapped events include a `_wrap` field with timing:

```jsonl
{"hook_event_name":"PostToolUse","tool_name":"Bash","_wrap":{"command":"lint.sh","exit_code":0,"duration_ms":120.5,"stdout":"...","stderr":""},...}
```

## Requirements

- Python >= 3.12
- Zero dependencies (stdlib only)

## Commands

### `cc-obs install`

Adds observer hooks to Claude Code settings for all lifecycle events. Idempotent — safe to run repeatedly. Existing non-cc-obs hooks are preserved.

```sh
cc-obs install            # write to .claude/settings.local.json (default)
cc-obs install --project  # write to .claude/settings.json instead
cc-obs install --uninstall  # remove all cc-obs hooks
```

| Flag | Description |
|------|-------------|
| `--project` | Target the shared `settings.json` instead of `settings.local.json` |
| `--uninstall` | Remove all cc-obs hook entries, leaving other hooks intact |

The installed hooks cover: `SessionStart`, `Stop`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `PreCompact`, `Notification`, `PermissionRequest`, `TeammateIdle`, `TaskCompleted`.

### `cc-obs log`

The hook handler invoked by every installed hook. Not typically called directly.

```sh
echo '{"hook_event_name":"test","cwd":"/tmp"}' | cc-obs log
```

Reads the hook JSON from stdin, adds `_ts` (ISO 8601 UTC timestamp) and `_seq` (sequence number), then appends to `.claude/cc-obs/events.jsonl`. Produces no output and always exits 0 — it's a silent observer.

The project root is determined from the `cwd` field in the hook JSON by walking up to find a `.claude/` directory.

### `cc-obs wrap`

Transparent wrapper that adds timing and I/O capture to an existing hook command. The wrapped command's behavior is unchanged — stdin is forwarded, stdout/stderr are passed through, and the exit code is preserved.

```sh
cc-obs wrap -- your-command --flag
```

The wrapper logs an enriched event with a `_wrap` field containing:

| Field | Description |
|-------|-------------|
| `command` | The wrapped command string |
| `exit_code` | The command's exit code |
| `duration_ms` | Execution time in milliseconds |
| `stdout` | Captured stdout |
| `stderr` | Captured stderr |

Use it in hook config to instrument existing hooks without modifying them:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "command": "cc-obs wrap -- ./my-lint-hook.sh"
      }
    ]
  }
}
```

### `cc-obs view`

Generates a self-contained HTML file from the session log and opens it in your default browser.

```sh
cc-obs view           # generate and open
cc-obs view --no-open # generate only
```

| Flag | Description |
|------|-------------|
| `--no-open` | Write `.claude/cc-obs/view.html` without opening the browser |

The viewer has three sections:

- **Dashboard** — session ID, model, event counts by type, tool usage frequency, total hook execution time (from wrapped events)
- **Timeline** — chronological event list with color-coded badges, relative timestamps, thinking gaps between events, tool call summaries, and expandable JSON payloads. Filterable by event type and searchable.
- **Agent tree** — subagent hierarchy derived from SubagentStart/SubagentStop events, with per-agent event lists

### `cc-obs status`

Prints a summary of the current session log.

```sh
cc-obs status
```

Output includes:

- Session ID and model
- Total event count and log file size
- Time span of the session
- Event count breakdown by type
- Tool usage frequency
- Wrapped hook count and total execution time

Example:

```
Session: abc-123
Model:   claude-sonnet-4-5-20250929
Events:  42 (8.3 KB)
Span:    3.2m (2025-01-01T00:00:00+00:00 → 2025-01-01T00:03:12+00:00)

Events by type:
  PostToolUse: 12
  PreToolUse: 12
  UserPromptSubmit: 5
  ...

Tool usage:
  Bash: 8
  Read: 3
  Edit: 1
```

### `cc-obs clear`

Deletes the log and generated HTML files.

```sh
cc-obs clear          # delete with confirmation output
cc-obs clear --quiet  # delete silently (used by SessionStart hook)
```

| Flag | Description |
|------|-------------|
| `--quiet` | Suppress all output. Used internally by the SessionStart hook to clear logs at session start without noise. |

Removes `.claude/cc-obs/events.jsonl` and `.claude/cc-obs/view.html` if they exist.
