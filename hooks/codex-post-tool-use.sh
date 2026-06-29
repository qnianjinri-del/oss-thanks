#!/usr/bin/env bash
# Codex PostToolUse hook adapter for oss-thanks.

set -euo pipefail

root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python3 "$root/scripts/oss_thanks.py" hook
