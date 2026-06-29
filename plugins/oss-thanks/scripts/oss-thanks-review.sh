#!/usr/bin/env bash
# Print the pending thanks queue when a turn stops.

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$script_dir/oss_thanks.py" review
