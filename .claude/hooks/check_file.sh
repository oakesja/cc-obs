#!/bin/bash

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

uv run ruff check --fix "$FILE_PATH"
uv run ty check "$FILE_PATH"
