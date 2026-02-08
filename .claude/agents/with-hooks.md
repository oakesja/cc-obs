---
name: wiht-hooks
description: agent-with-hooks
tools: Read, Edit, Write, Bash, Grep, Glob
model: sonnet
skills:
- skill
hooks:
  PreToolUse:
  - matcher: Edit,Write
    hooks:
    - type: command
      command: cc-obs wrap --name "pre-tool" -- /scripts/pre-tool.sh
  PostToolUse:
  - matcher: Edit,Write
    hooks:
    - type: command
      command: cc-obs wrap --name "post-tool" -- :./scripts/post-tool.sh
  Stop:
  - hooks:
    - type: command,prompt,agent
      command: ./scripts/on-stop.sh
---

# Purpose

You are a <role-definition-for-new-agent>.

## Workflow
1. <Step-by-step instructions for the new agent.>
2. <...>
3. <...>

**Best Practices:**
- <List of best practices relevant to the new agent's domain.>
- <...>

## Report / Response

Provide your final response in a clear and organized manner.
