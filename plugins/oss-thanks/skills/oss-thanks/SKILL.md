---
name: oss-thanks
description: Track GitHub open-source repositories and agent skills that Codex references, clones, downloads, or installs during coding tasks, then either queue them for user review or star them only when explicit auto-star consent is configured. Use when working with GitHub projects, open-source dependencies, external skills, plugin downloads, repository research, or attribution/thanks workflows.
---

# OSS Thanks

Use this skill to make open-source usage visible while an agent works.

Resolve the CLI before running commands:

- If this skill is loaded from `plugins/oss-thanks/skills/oss-thanks`, use `plugins/oss-thanks/scripts/oss_thanks.py`.
- If this skill is loaded from `.agents/skills/oss-thanks`, use `scripts/oss_thanks.py` from the repository root.
- If unsure, locate it with `find .. -path '*/scripts/oss_thanks.py' -print`.

## Workflow

1. Detect GitHub repositories in commands, logs, README links, skill install URLs, package setup notes, or browser/search notes.
2. Record every detected repository with `scripts/oss_thanks.py record`.
3. Respect the configured consent mode:
   - `review`: record repositories and present them at the end for the user to approve.
   - `auto-star`: star detected repositories immediately only when `auto_star_consent` is enabled or the command uses `--yes`.
4. At the end of the task, run `scripts/oss_thanks.py review` and, when useful, `scripts/oss_thanks.py summary --output THANKS.md`.

## Commands

Initialize review mode:

```bash
python3 <path-to>/scripts/oss_thanks.py init --mode review
```

Initialize explicit auto-star mode:

```bash
python3 <path-to>/scripts/oss_thanks.py init --mode auto-star --yes
```

Record observed repositories:

```bash
python3 <path-to>/scripts/oss_thanks.py record --source codex --reason "referenced during implementation" --text "https://github.com/owner/repo"
```

Review pending repositories:

```bash
python3 <path-to>/scripts/oss_thanks.py review
```

Star pending repositories after user approval:

```bash
python3 <path-to>/scripts/oss_thanks.py review --star --yes
```

## Guardrails

- Keep `review` as the default mode.
- Do not enable `auto-star` unless the user explicitly requested it for their own GitHub account.
- Do not star private, internal, or ambiguous repositories unless the user explicitly confirms.
- If GitHub authentication is unavailable, keep repositories pending and report the auth issue.
- Use `--dry-run` when demonstrating the workflow or validating hooks.

## Hook Usage

When a Codex hook payload is available, pipe it to:

```bash
python3 <path-to>/scripts/oss_thanks.py hook
```

Use `examples/codex-hooks.json` as a starting point for project-level Codex hooks.
