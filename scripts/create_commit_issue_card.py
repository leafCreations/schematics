#!/usr/bin/env python3
"""Create a kanban commit-issue card when pre-commit fails.

Ruff hook failures: parse rule ids (e.g. SIM110) into frontmatter `ruffRules` and `## Ruff rules`.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FEATURES_DIR = REPO_ROOT / ".devtool" / "features"

_HOOK_TITLES = {
    "ruff": "Pre-commit ruff failed",
    "validate-palettes": "Pre-commit palette validation failed",
    "pytest": "Pre-commit pytest failed",
}

_FAILED_TEST_RE = re.compile(r"^FAILED (tests/[^\s:]+\.py)", re.MULTILINE)
_RUFF_RULE_LINE_RE = re.compile(r"^([A-Z]+\d+)\s", re.MULTILINE)
_RUFF_RULE_LOCATION_RE = re.compile(r":\d+:\d+:\s*([A-Z]+\d+)\b")
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
_ORDER_RE = re.compile(r'^order:\s*"([^"]+)"', re.MULTILINE)
_STATUS_RE = re.compile(r'^status:\s*"([^"]+)"', re.MULTILINE)


def _read_frontmatter(path: Path) -> tuple[str | None, str | None]:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None, None
    body = match.group(1)
    status = _STATUS_RE.search(body)
    order = _ORDER_RE.search(body)
    return (
        status.group(1) if status else None,
        order.group(1) if order else None,
    )


def _increment_order(order: str) -> str:
    if not order:
        return "a0"
    prefix, last = order[:-1], order[-1]
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    idx = chars.find(last)
    if idx < 0 or idx + 1 >= len(chars):
        return order + "0"
    return prefix + chars[idx + 1]


def _next_order(features_dir: Path, *, status: str = "todo") -> str:
    orders: list[str] = []
    if features_dir.is_dir():
        for path in features_dir.glob("*.md"):
            card_status, order = _read_frontmatter(path)
            if card_status == status and order:
                orders.append(order)
    if not orders:
        return "a0"
    orders.sort()
    return _increment_order(orders[-1])


def _extract_failed_test_files(log_text: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for match in _FAILED_TEST_RE.finditer(log_text):
        path = match.group(1)
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def _extract_ruff_rule_ids(log_text: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for pattern in (_RUFF_RULE_LINE_RE, _RUFF_RULE_LOCATION_RE):
        for match in pattern.finditer(log_text):
            code = match.group(1)
            if code not in seen:
                seen.add(code)
                ordered.append(code)
    return ordered


def _problem_excerpt(log_text: str, *, max_lines: int = 60) -> str:
    lines = [line.rstrip() for line in log_text.splitlines() if line.strip()]
    if not lines:
        return "Pre-commit hook failed with no captured output."
    tail = lines[-max_lines:]
    return "\n".join(tail)


def _staged_python_files() -> list[str]:
    import subprocess

    result = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACM",
            "--",
            "*.py",
            "*.pyi",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _staged_files_summary() -> str:
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "(could not read staged files)"
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return "(no staged files)"
    return "\n".join(f"- `{path}`" for path in lines)


def build_card_body(
    *,
    hook: str,
    log_text: str,
    failed_test_files: list[str] | None = None,
    ruff_rules: list[str] | None = None,
) -> tuple[str, str, str]:
    title = _HOOK_TITLES.get(hook, f"Pre-commit {hook} failed")
    problem = _problem_excerpt(log_text)

    if failed_test_files is None:
        if hook == "pytest":
            failed_test_files = _extract_failed_test_files(log_text)
        elif hook == "ruff":
            failed_test_files = _staged_python_files()
        else:
            failed_test_files = []

    if ruff_rules is None and hook == "ruff":
        ruff_rules = _extract_ruff_rule_ids(log_text)
    elif ruff_rules is None:
        ruff_rules = []

    if failed_test_files:
        failed_tests = "\n".join(f"- `{path}`" for path in failed_test_files)
    else:
        failed_tests = "- _(none identified — see Problem)_"

    ruff_rules_section = ""
    if ruff_rules:
        bullets = "\n".join(f"- `{code}`" for code in ruff_rules)
        ruff_rules_section = f"""
## Ruff rules

{bullets}
"""

    body = f"""# {title}

Captured automatically when `git commit` failed on the **{hook}** pre-commit hook.
{ruff_rules_section}
## Problem

```
{problem}
```

## Failed Tests

{failed_tests}

## Staged files

{_staged_files_summary()}
"""
    return title, problem, body


def create_commit_issue_card(
    *,
    hook: str,
    log_text: str,
    features_dir: Path | None = None,
) -> Path:
    features_dir = features_dir or DEFAULT_FEATURES_DIR
    features_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    stamp = now.strftime("%Y-%m-%dT%H%M%S")
    card_id = f"commit-issue-{hook}-{stamp}"
    title, _, body = build_card_body(hook=hook, log_text=log_text)
    ruff_rules = _extract_ruff_rule_ids(log_text) if hook == "ruff" else []

    created = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    order = _next_order(features_dir)

    ruff_rules_line = ""
    if ruff_rules:
        quoted = ", ".join(f'"{code}"' for code in ruff_rules)
        ruff_rules_line = f"ruffRules: [{quoted}]\n"

    frontmatter = f"""---
id: "{card_id}"
status: "todo"
priority: "high"
assignee: null
dueDate: null
created: "{created}"
modified: "{created}"
completedAt: null
labels: ["commit-issue"]
{ruff_rules_line}order: "{order}"
---
"""

    path = features_dir / f"{card_id}.md"
    path.write_text(frontmatter + body, encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--hook",
        required=True,
        choices=sorted(_HOOK_TITLES),
        help="Pre-commit hook that failed",
    )
    parser.add_argument("--log", required=True, type=Path, help="Captured hook output log")
    parser.add_argument(
        "--features-dir",
        type=Path,
        default=DEFAULT_FEATURES_DIR,
        help="Kanban features directory (default: .devtool/features)",
    )
    args = parser.parse_args(argv)

    if not args.log.is_file():
        print(f"create_commit_issue_card: log not found: {args.log}", file=sys.stderr)
        return 1

    log_text = args.log.read_text(encoding="utf-8", errors="replace")
    path = create_commit_issue_card(
        hook=args.hook,
        log_text=log_text,
        features_dir=args.features_dir,
    )
    try:
        display = path.relative_to(REPO_ROOT)
    except ValueError:
        display = path
    print(f"commit-issue card created: {display}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
