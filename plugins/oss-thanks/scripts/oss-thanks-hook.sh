#!/usr/bin/env bash
# Plugin hook adapter. Reads Codex hook JSON from stdin.

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$script_dir/oss_thanks.py" hook
