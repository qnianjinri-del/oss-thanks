---
name: oss-thanks
description: Track GitHub repositories that Codex actually uses during coding tasks, then auto-star them or queue them for final review based on the user's saved preference. Use when cloning GitHub repos, installing GitHub skills/plugins/templates, downloading from GitHub, or explicitly opening and referencing a GitHub repository during implementation.
---

# OSS Thanks

Use this skill when an AI coding task actually uses a GitHub repository and should record it for auto-star or final review.

Resolve the CLI before running commands:

- If this skill is loaded from `plugins/oss-thanks/skills/oss-thanks`, use `plugins/oss-thanks/scripts/oss_thanks.py`.
- If this skill is loaded from `.agents/skills/oss-thanks`, use `scripts/oss_thanks.py` from the repository root.
- If unsure, locate it with `find .. -path '*/scripts/oss_thanks.py' -print`.

## First Use

Before the first real use in a project, run:

```bash
python3 <path-to>/scripts/oss_thanks.py status
```

If it says `Configured: no`, ask the user exactly:

```text
OSS Thanks 要怎么运行？

1. 自动点 star
2. 先问我
```

Save the answer once:

```bash
python3 <path-to>/scripts/oss_thanks.py setup --mode auto-star
python3 <path-to>/scripts/oss_thanks.py setup --mode review
```

Do not ask again after the choice is saved.

## What Counts

Record only actual GitHub repo use:

- `git clone` of a GitHub repo
- `gh repo clone owner/repo`
- GitHub HTTPS or SSH repo links used for clone, download, or install
- Installing a GitHub skill, plugin, or template
- Explicitly opening and referencing a GitHub repo during implementation

Do not record a repo just because it appears in search results, a web page, or incidental text.

## Workflow

1. When actual GitHub repo use happens, call `record` with the command or note that proves use.
2. If mode is `auto-star`, the script attempts to star immediately.
3. If mode is `review`, run `review` near the end of the task and show the pending list before finishing.

## Commands

Record observed repo use:

```bash
python3 <path-to>/scripts/oss_thanks.py record --source codex --reason "used during implementation" --text "git clone https://github.com/owner/repo.git"
```

Show saved mode:

```bash
python3 <path-to>/scripts/oss_thanks.py status
```

Review pending repositories:

```bash
python3 <path-to>/scripts/oss_thanks.py review
```

Star pending repositories after user approval:

```bash
python3 <path-to>/scripts/oss_thanks.py review --star --yes
```

Ignore a repository:

```bash
python3 <path-to>/scripts/oss_thanks.py ignore owner/repo
```

## Guardrails

- Keep the project focused on GitHub stars for repos actually used by AI coding tools.
- Do not add thanks text, issue posting, reports, governance flows, or broad contribution-platform behavior.
- Do not enable `auto-star` unless the user chose it for their own GitHub account.
- If GitHub authentication is unavailable, keep repositories pending and report that the user needs `gh auth login` or `GH_TOKEN` / `GITHUB_TOKEN`.
- Use `--dry-run` when demonstrating the workflow or validating hooks.

## Hook Usage

When a Codex hook payload is available, pipe it to:

```bash
python3 <path-to>/scripts/oss_thanks.py hook
```
