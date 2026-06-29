# OSS Thanks

OSS Thanks helps AI coding assistants make open-source usage visible.

When Codex, Claude Code, or another agent references a GitHub repository, clones a project, or downloads a skill from GitHub, this tool records the repository locally. Users can choose one of two consent modes:

- `review`: collect repositories during the task, then show the queue for human approval.
- `auto-star`: star detected repositories immediately from the user's GitHub account after explicit opt-in.

The default is `review`.

## Install As A Codex Plugin

After this repository is on GitHub, add it as a Codex plugin marketplace:

```bash
codex plugin marketplace add qnianjinri-del/oss-thanks
```

Then open Codex Plugins, install **OSS Thanks**, and start a new thread.

This repository also includes the plugin source directly at:

```text
plugins/oss-thanks
```

## Quick Start

```bash
python3 scripts/oss_thanks.py init --mode review
python3 scripts/oss_thanks.py record --text "git clone https://github.com/pallets/flask.git"
python3 scripts/oss_thanks.py review
python3 scripts/oss_thanks.py review --star --yes
```

Enable direct auto-star only after the user chooses it:

```bash
python3 scripts/oss_thanks.py init --mode auto-star --yes
```

Authentication uses the GitHub CLI first:

```bash
gh auth login
```

If `gh` is unavailable, set `GH_TOKEN` or `GITHUB_TOKEN` with permission to star repositories.

## Codex Skill

The repo includes a Codex skill at:

```text
.agents/skills/oss-thanks
plugins/oss-thanks/skills/oss-thanks
```

The skill tells Codex when to record GitHub repositories and how to respect the chosen consent mode.

## Codex Hook Adapter

For automatic collection from Codex shell commands, adapt `examples/codex-hooks.json` into your trusted Codex hook configuration.

The hook adapter reads Codex hook JSON from stdin and records repositories found in any string field:

```bash
hooks/codex-post-tool-use.sh
```

Keep hook installation explicit. Hooks can run commands automatically, so users should review and trust the exact hook before enabling it.

The packaged plugin also includes hook definitions at:

```text
plugins/oss-thanks/hooks/hooks.json
```

## Files

- `scripts/oss_thanks.py`: core CLI and GitHub star implementation.
- `.agents/skills/oss-thanks/SKILL.md`: Codex skill.
- `plugins/oss-thanks`: installable Codex plugin package.
- `.agents/plugins/marketplace.json`: repo marketplace entry.
- `examples/codex-hooks.json`: example Codex hook config.
- `hooks/codex-post-tool-use.sh`: hook adapter.

## Design Principles

- Make open-source usage visible.
- Prefer review and human approval by default.
- Allow auto-star only as a clear user choice.
- Keep a local attribution log even when GitHub authentication is unavailable.
