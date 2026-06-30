#!/usr/bin/env python3
"""Track GitHub repositories an agent uses and optionally star them."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


STATE_VERSION = 1
CONFIG_VERSION = 1
DEFAULT_HOME = ".oss-thanks"
STATE_NAME = "events.json"
CONFIG_NAME = "config.json"
MODE_REVIEW = "review"
MODE_AUTO = "auto-star"
VALID_MODES = {MODE_REVIEW, MODE_AUTO}

GITHUB_URL_RE = re.compile(
    r"(?:https?://)?github\.com[:/](?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
GITHUB_SSH_RE = re.compile(
    r"git@github\.com:(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
GH_REPO_COMMAND_RE = re.compile(
    r"\bgh\s+repo\s+clone\s+(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
GIT_CLONE_GITHUB_RE = re.compile(
    r"\bgit\s+clone\b[^\n]*?(?:https?://)?github\.com[:/](?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
GIT_CLONE_SSH_RE = re.compile(
    r"\bgit\s+clone\b[^\n]*?git@github\.com:(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
USE_CONTEXT_RE = re.compile(
    r"\b("
    r"clone|cloned|cloning|download|downloaded|downloading|install|installed|installing|"
    r"open|opened|opening|reference|referenced|referencing|read|reading|inspect|inspected|"
    r"browse|browsed|used|using|fetch|fetched|template|plugin|skill|"
    r"pip|npm|pnpm|yarn|uv|curl|wget"
    r")\b|克隆|下载|安装|打开|参考|引用|使用|用到",
    re.IGNORECASE,
)

RESERVED_GITHUB_PATHS = {
    "about",
    "account",
    "apps",
    "blog",
    "codespaces",
    "collections",
    "contact",
    "customer-stories",
    "dashboard",
    "enterprise",
    "events",
    "explore",
    "features",
    "issues",
    "login",
    "marketplace",
    "new",
    "notifications",
    "orgs",
    "pricing",
    "pulls",
    "search",
    "settings",
    "sponsors",
    "topics",
    "trending",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def get_home(path: str | None = None) -> Path:
    if path:
        return Path(path)
    if os.environ.get("OSS_THANKS_HOME"):
        return Path(os.environ["OSS_THANKS_HOME"])
    return Path.cwd() / DEFAULT_HOME


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default.copy()
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    tmp_path.replace(path)


def default_config() -> dict[str, Any]:
    return {
        "version": CONFIG_VERSION,
        "mode": MODE_REVIEW,
        "auto_star_consent": False,
        "dry_run": False,
        "star_method": "auto",
        "ignored_repos": [],
    }


def load_config(home: Path) -> dict[str, Any]:
    config = default_config()
    config_path = home / CONFIG_NAME
    saved_config = load_json(config_path, {})
    config.update(saved_config)
    if config_path.exists() and "configured" not in saved_config:
        config["configured"] = True

    env_mode = os.environ.get("OSS_THANKS_MODE")
    if env_mode:
        config["mode"] = env_mode
    if os.environ.get("OSS_THANKS_AUTO_STAR") is not None:
        config["auto_star_consent"] = truthy(os.environ.get("OSS_THANKS_AUTO_STAR"))
    if os.environ.get("OSS_THANKS_DRY_RUN") is not None:
        config["dry_run"] = truthy(os.environ.get("OSS_THANKS_DRY_RUN"))

    if config.get("mode") not in VALID_MODES:
        raise ValueError(f"Invalid mode {config.get('mode')!r}. Use review or auto-star.")
    return config


def config_exists(home: Path) -> bool:
    return (home / CONFIG_NAME).exists()


def save_config(
    home: Path,
    *,
    mode: str,
    dry_run: bool = False,
    star_method: str = "auto",
) -> dict[str, Any]:
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode {mode!r}. Use review or auto-star.")
    config = default_config()
    config.update(
        {
            "configured": True,
            "configured_at": utc_now(),
            "mode": mode,
            "auto_star_consent": mode == MODE_AUTO,
            "dry_run": dry_run,
            "star_method": star_method,
        }
    )
    save_json(home / CONFIG_NAME, config)
    save_json(home / STATE_NAME, load_state(home))
    return config


def prompt_for_mode(default: str = MODE_AUTO) -> str:
    print("")
    print("OSS Thanks 要怎么运行？")
    print("")
    print("1. 自动点 star")
    print("2. 先问我")
    print("")
    print("选过一次后会记住。")
    answer = input(f"请选择 1 或 2 [{1 if default == MODE_AUTO else 2}]: ").strip().lower()
    if not answer:
        return default
    if answer in {"1", "auto", "auto-star", "star", "自动", "自动点"}:
        return MODE_AUTO
    if answer in {"2", "review", "ask", "manual", "确认", "先问"}:
        return MODE_REVIEW
    print("没看懂这个选择，先按“先问我”保存。")
    return MODE_REVIEW


def ensure_config_for_interactive_record(home: Path, args: argparse.Namespace) -> dict[str, Any]:
    if config_exists(home) or not sys.stdin.isatty() or getattr(args, "mode", None):
        return load_config(home)
    mode = prompt_for_mode()
    return save_config(home, mode=mode, dry_run=getattr(args, "dry_run", False))


def default_state() -> dict[str, Any]:
    return {"version": STATE_VERSION, "repos": {}}


def load_state(home: Path) -> dict[str, Any]:
    state = load_json(home / STATE_NAME, default_state())
    state.setdefault("version", STATE_VERSION)
    state.setdefault("repos", {})
    return state


def normalize_repo(owner: str, repo: str) -> str | None:
    owner = owner.strip().strip("/").strip(").,;:'\"`")
    repo = repo.strip().strip("/").strip(").,;:'\"`")
    if repo.endswith(".git"):
        repo = repo[:-4]
    repo = repo.split("#", 1)[0].split("?", 1)[0]
    if not owner or not repo:
        return None
    if owner.lower() in RESERVED_GITHUB_PATHS:
        return None
    if "/" in owner or "/" in repo:
        return None
    return f"{owner}/{repo}"


def line_indicates_repo_use(line: str) -> bool:
    return bool(USE_CONTEXT_RE.search(line))


def extract_repos(text: str) -> list[str]:
    found: set[str] = set()

    for line in text.splitlines():
        for pattern in (GIT_CLONE_GITHUB_RE, GIT_CLONE_SSH_RE):
            for match in pattern.finditer(line):
                repo = normalize_repo(match.group("owner"), match.group("repo"))
                if repo:
                    found.add(repo)

        for match in GH_REPO_COMMAND_RE.finditer(line):
            full = match.group("repo")
            owner, repo_name = full.split("/", 1)
            repo = normalize_repo(owner, repo_name)
            if repo:
                found.add(repo)

        if not line_indicates_repo_use(line):
            continue

        for pattern in (GITHUB_URL_RE, GITHUB_SSH_RE):
            for match in pattern.finditer(line):
                repo = normalize_repo(match.group("owner"), match.group("repo"))
                if repo:
                    found.add(repo)

    return sorted(found, key=str.lower)


def flatten_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from flatten_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from flatten_strings(item)


def extract_text_from_hook_payload(payload: str) -> str:
    if not payload.strip():
        return ""
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError:
        return payload
    return "\n".join(flatten_strings(decoded))


def read_input_text(args: argparse.Namespace) -> str:
    chunks: list[str] = []
    for text in args.text or []:
        chunks.append(text)
    for file_name in args.file or []:
        chunks.append(Path(file_name).read_text(encoding="utf-8"))
    if not chunks and not sys.stdin.isatty():
        chunks.append(sys.stdin.read())
    return "\n".join(chunks)


def record_repositories(
    home: Path,
    repos: Iterable[str],
    *,
    source: str,
    reason: str,
    mode: str,
) -> dict[str, Any]:
    state = load_state(home)
    now = utc_now()

    for repo in repos:
        entry = state["repos"].setdefault(
            repo,
            {
                "repo": repo,
                "first_seen": now,
                "last_seen": now,
                "status": "pending",
                "sources": [],
            },
        )
        entry["last_seen"] = now
        if entry.get("status") not in {"starred", "ignored"}:
            entry["status"] = "pending"
        entry.setdefault("sources", []).append(
            {
                "at": now,
                "source": source,
                "reason": reason,
                "mode": mode,
            }
        )

    save_json(home / STATE_NAME, state)
    return state


def pending_repos(state: dict[str, Any]) -> list[dict[str, Any]]:
    repos = state.get("repos", {})
    return [
        entry
        for entry in sorted(repos.values(), key=lambda item: item.get("repo", "").lower())
        if entry.get("status") == "pending"
    ]


def all_repos(state: dict[str, Any]) -> list[dict[str, Any]]:
    repos = state.get("repos", {})
    return sorted(repos.values(), key=lambda item: item.get("repo", "").lower())


def star_with_gh(repo: str) -> tuple[bool, str]:
    gh = shutil.which("gh")
    if not gh:
        return False, "GitHub CLI `gh` was not found. Install gh and run `gh auth login`, or set GH_TOKEN/GITHUB_TOKEN."
    completed = subprocess.run(
        [gh, "repo", "star", repo],
        check=False,
        capture_output=True,
        text=True,
    )
    output = (completed.stdout + completed.stderr).strip()
    if completed.returncode == 0:
        return True, output or "starred with gh"
    return False, output or f"gh exited with code {completed.returncode}"


def star_with_api(repo: str) -> tuple[bool, str]:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        return False, "GitHub auth is missing. Run `gh auth login` or set GH_TOKEN/GITHUB_TOKEN."
    url = f"https://api.github.com/user/starred/{repo}"
    request = urllib.request.Request(
        url,
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "oss-thanks",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status in {204, 304}:
                return True, "starred with GitHub API"
            return False, f"GitHub API returned HTTP {response.status}"
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        return False, f"GitHub API returned HTTP {error.code}: {detail}"
    except urllib.error.URLError as error:
        return False, f"GitHub API request failed: {error}"


def star_repo(repo: str, config: dict[str, Any], dry_run: bool = False) -> tuple[bool, str]:
    if dry_run or config.get("dry_run"):
        return True, "dry-run: would star"

    method = config.get("star_method", "auto")
    if method in {"auto", "gh"}:
        ok, message = star_with_gh(repo)
        if ok or method == "gh":
            return ok, message
    if method in {"auto", "api"}:
        return star_with_api(repo)
    return False, f"Unknown star_method {method!r}"


def update_star_status(
    home: Path,
    repos: Iterable[str],
    config: dict[str, Any],
    *,
    dry_run: bool = False,
) -> int:
    state = load_state(home)
    exit_code = 0
    for repo in repos:
        if repo not in state.get("repos", {}):
            record_repositories(home, [repo], source="manual", reason="manual star request", mode="manual")
            state = load_state(home)

        ok, message = star_repo(repo, config, dry_run=dry_run)
        entry = state["repos"][repo]
        if ok:
            entry["status"] = "starred" if "dry-run" not in message else "pending"
            entry["starred_at"] = utc_now() if "dry-run" not in message else None
            entry["last_error"] = None
            print(f"[oss-thanks] {repo}: {message}")
        else:
            entry["status"] = "pending"
            entry["last_error"] = message
            exit_code = 1
            print(f"[oss-thanks] {repo}: {message}", file=sys.stderr)
    save_json(home / STATE_NAME, state)
    return exit_code


def command_init(args: argparse.Namespace) -> int:
    home = get_home(args.home)
    mode = args.mode
    if mode == MODE_AUTO and not args.yes:
        print(
            "Refusing to enable auto-star without --yes. "
            "This mode will star repositories from your GitHub account.",
            file=sys.stderr,
        )
        return 2
    save_config(home, mode=mode, dry_run=args.dry_run, star_method=args.star_method)
    print(f"[oss-thanks] initialized {home} in {mode} mode")
    return 0


def command_setup(args: argparse.Namespace) -> int:
    home = get_home(args.home)
    if args.mode:
        mode = args.mode
    else:
        if not sys.stdin.isatty():
            print("Use --mode auto-star or --mode review in non-interactive setup.", file=sys.stderr)
            return 2
        mode = prompt_for_mode(default=MODE_AUTO)
    save_config(home, mode=mode, dry_run=args.dry_run, star_method=args.star_method)
    if mode == MODE_AUTO:
        print("[oss-thanks] saved: auto-star. Repos actually used during the project will be starred automatically.")
    else:
        print("[oss-thanks] saved: review. Repos actually used during the project will be shown before the task ends.")
    return 0


def command_status(args: argparse.Namespace) -> int:
    home = get_home(args.home)
    config = load_config(home)
    state = load_state(home)
    pending = pending_repos(state)
    configured = "yes" if config_exists(home) and config.get("configured", False) else "no"
    print(f"Home: {home}")
    print(f"Configured: {configured}")
    print(f"Mode: {config['mode']}")
    print(f"Auto-star consent: {'on' if config.get('auto_star_consent') else 'off'}")
    print(f"Pending repos: {len(pending)}")
    return 0


def command_record(args: argparse.Namespace) -> int:
    home = get_home(args.home)
    config = ensure_config_for_interactive_record(home, args)
    mode = args.mode or config["mode"]
    text = read_input_text(args)
    repos = extract_repos(text)
    ignored = set(config.get("ignored_repos", []))
    repos = [repo for repo in repos if repo not in ignored]

    if not repos:
        print("[oss-thanks] no actual GitHub repository use detected")
        return 0

    record_repositories(home, repos, source=args.source, reason=args.reason, mode=mode)
    print(f"[oss-thanks] recorded {len(repos)} repo(s): {', '.join(repos)}")

    if mode == MODE_AUTO:
        if args.yes or config.get("auto_star_consent"):
            return update_star_status(home, repos, config, dry_run=args.dry_run)
        print(
            "[oss-thanks] auto-star mode was requested, but consent is not enabled. "
            "Run `oss_thanks.py setup --mode auto-star` or set OSS_THANKS_AUTO_STAR=1.",
            file=sys.stderr,
        )
    return 0


def command_hook(args: argparse.Namespace) -> int:
    payload = sys.stdin.read()
    text = extract_text_from_hook_payload(payload)
    args.text = [text]
    args.file = []
    args.source = args.source or "codex-hook"
    args.reason = args.reason or "agent tool event"
    return command_record(args)


def command_review(args: argparse.Namespace) -> int:
    home = get_home(args.home)
    state = load_state(home)
    config = load_config(home)
    pending = pending_repos(state)

    if args.format == "json":
        print(json.dumps(pending, indent=2, sort_keys=True))
    elif args.format == "md":
        for entry in pending:
            print(f"- [{entry['repo']}](https://github.com/{entry['repo']})")
    else:
        if not pending:
            if config.get("mode") == MODE_AUTO and config.get("auto_star_consent"):
                print("[oss-thanks] no pending repositories; auto-star mode is on")
            else:
                print("[oss-thanks] no pending repositories")
        else:
            print("Pending repositories:")
            for entry in pending:
                print(
                    f"- {entry['repo']} "
                    f"(seen {len(entry.get('sources', []))} time(s), first {entry.get('first_seen')})"
                )

    if args.star:
        if not args.yes:
            print("Refusing to star from review without --yes.", file=sys.stderr)
            return 2
        return update_star_status(home, [entry["repo"] for entry in pending], config, dry_run=args.dry_run)
    return 0


def command_star(args: argparse.Namespace) -> int:
    home = get_home(args.home)
    config = load_config(home)
    if not args.yes:
        print("Refusing to star without --yes.", file=sys.stderr)
        return 2

    if args.all:
        repos = [entry["repo"] for entry in pending_repos(load_state(home))]
    else:
        repos = args.repos
    if not repos:
        print("[oss-thanks] no repositories to star")
        return 0
    return update_star_status(home, repos, config, dry_run=args.dry_run)


def command_ignore(args: argparse.Namespace) -> int:
    home = get_home(args.home)
    state = load_state(home)
    for repo in args.repos:
        normalized = normalize_repo(*repo.split("/", 1)) if "/" in repo else None
        if not normalized:
            print(f"Invalid repository: {repo}", file=sys.stderr)
            return 2
        entry = state["repos"].setdefault(
            normalized,
            {
                "repo": normalized,
                "first_seen": utc_now(),
                "last_seen": utc_now(),
                "sources": [],
            },
        )
        entry["status"] = "ignored"
    save_json(home / STATE_NAME, state)
    print(f"[oss-thanks] ignored {len(args.repos)} repo(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", help="State directory. Defaults to ./ .oss-thanks or OSS_THANKS_HOME.")
    with_home = argparse.ArgumentParser(add_help=False)
    with_home.add_argument("--home", help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", parents=[with_home], help="Create config and state files.")
    init.add_argument("--mode", choices=sorted(VALID_MODES), default=MODE_REVIEW)
    init.add_argument("--star-method", choices=["auto", "gh", "api"], default="auto")
    init.add_argument("--dry-run", action="store_true", help="Record only; do not call GitHub.")
    init.add_argument("--yes", action="store_true", help="Confirm auto-star consent when mode is auto-star.")
    init.set_defaults(func=command_init)

    setup = subparsers.add_parser("setup", parents=[with_home], help="Ask how OSS Thanks should run and remember the choice.")
    setup.add_argument("--mode", choices=sorted(VALID_MODES), help="Save a mode without prompting.")
    setup.add_argument("--star-method", choices=["auto", "gh", "api"], default="auto")
    setup.add_argument("--dry-run", action="store_true", help="Record only; do not call GitHub.")
    setup.set_defaults(func=command_setup)

    status = subparsers.add_parser("status", parents=[with_home], help="Show saved OSS Thanks mode and queue size.")
    status.set_defaults(func=command_status)

    record = subparsers.add_parser("record", parents=[with_home], help="Record actual GitHub repo use found in text, files, or stdin.")
    record.add_argument("--text", action="append", help="Text to scan for GitHub repositories.")
    record.add_argument("--file", action="append", help="File to scan for GitHub repositories.")
    record.add_argument("--source", default="manual", help="Where this observation came from.")
    record.add_argument("--reason", default="used by agent", help="Why the repository is being recorded.")
    record.add_argument("--mode", choices=sorted(VALID_MODES), help="Override configured consent mode.")
    record.add_argument("--dry-run", action="store_true", help="Do not call GitHub even in auto-star mode.")
    record.add_argument("--yes", action="store_true", help="Confirm auto-star for this command.")
    record.set_defaults(func=command_record)

    hook = subparsers.add_parser("hook", parents=[with_home], help="Read a Codex/agent hook payload from stdin and record repos.")
    hook.add_argument("--source", default="codex-hook")
    hook.add_argument("--reason", default="agent tool event")
    hook.add_argument("--mode", choices=sorted(VALID_MODES), help="Override configured consent mode.")
    hook.add_argument("--dry-run", action="store_true")
    hook.add_argument("--yes", action="store_true")
    hook.set_defaults(func=command_hook)

    review = subparsers.add_parser("review", parents=[with_home], help="Show pending repositories for user approval.")
    review.add_argument("--format", choices=["text", "json", "md"], default="text")
    review.add_argument("--star", action="store_true", help="Star all pending repositories.")
    review.add_argument("--dry-run", action="store_true")
    review.add_argument("--yes", action="store_true", help="Confirm starring all pending repositories.")
    review.set_defaults(func=command_review)

    star = subparsers.add_parser("star", parents=[with_home], help="Star selected repositories.")
    star.add_argument("repos", nargs="*", help="Repositories in owner/name form.")
    star.add_argument("--all", action="store_true", help="Star all pending repositories.")
    star.add_argument("--dry-run", action="store_true")
    star.add_argument("--yes", action="store_true", help="Confirm GitHub star operation.")
    star.set_defaults(func=command_star)

    ignore = subparsers.add_parser("ignore", parents=[with_home], help="Mark repositories as ignored.")
    ignore.add_argument("repos", nargs="+", help="Repositories in owner/name form.")
    ignore.set_defaults(func=command_ignore)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        print(f"oss-thanks: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
