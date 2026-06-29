---
name: oss-thanks
description: Track GitHub open-source repositories and agent skills that Codex references, clones, downloads, or installs during coding tasks, then auto-star them or queue them for final review based on the user's saved preference. Use when working with GitHub projects, open-source dependencies, external skills, plugin downloads, repository research, or automatic GitHub star workflows.
---

# OSS Thanks

Use this skill to star open-source GitHub repositories an agent uses.

Resolve the CLI before running commands:

- If this skill is loaded from `plugins/oss-thanks/skills/oss-thanks`, use `plugins/oss-thanks/scripts/oss_thanks.py`.
- If this skill is loaded from `.agents/skills/oss-thanks`, use `scripts/oss_thanks.py` from the repository root.
- If unsure, locate it with `find .. -path '*/scripts/oss_thanks.py' -print`.

## Workflow

1. Before the first real use in a project, run `python3 <path-to>/scripts/oss_thanks.py status`.
2. If it says `Configured: no`, ask the user directly:
   "OSS Thanks 要怎么运行？1. 自动点 star；2. 任务结束前让我确认。选过一次后我会记住。"
3. Save the answer with `setup --mode auto-star` or `setup --mode review`.
4. Detect GitHub repositories in commands, logs, README links, skill install URLs, package setup notes, or browser/search notes.
5. Record every detected repository with `record`.
6. If mode is `auto-star`, the script stars detected repositories automatically. If mode is `review`, run `review` near the end and ask whether to star the pending list.

## Commands

Ask and remember the user's preference:

```bash
python3 <path-to>/scripts/oss_thanks.py setup
```

Save auto-star mode directly after the user chooses it:

```bash
python3 <path-to>/scripts/oss_thanks.py setup --mode auto-star
```

Show saved mode:

```bash
python3 <path-to>/scripts/oss_thanks.py status
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

- The project is about auto-starring GitHub repositories used by AI tools; keep that as the primary path.
- Do not silently choose between modes in conversation. Ask once, save the answer, and reuse it.
- Do not enable `auto-star` unless the user chose it for their own GitHub account.
- Do not star private, internal, or ambiguous repositories unless the user explicitly confirms.
- If GitHub authentication is unavailable, keep repositories pending and report the auth issue.
- Use `--dry-run` when demonstrating the workflow or validating hooks.

## Hook Usage

When a Codex hook payload is available, pipe it to:

```bash
python3 <path-to>/scripts/oss_thanks.py hook
```

Use `examples/codex-hooks.json` as a starting point for project-level Codex hooks.
