#!/usr/bin/env python3
"""Create a fresh todo AGENTS.md governance audit kanban card."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FEATURES_DIR = REPO_ROOT / ".devtool" / "features"

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


_CHECKLIST = (
    "- [ ] **Routing:** [AGENTS.md](../../AGENTS.md) Every turn (steps 1–5, 1b) ↔ "
    "[agent-triage/SKILL.md](../../.cursor/skills/agent-triage/SKILL.md) §1/§1b ↔ "
    "[agent-routing.mdc](../../.cursor/rules/agent-routing.mdc) lifecycle\n"
    "- [ ] **Classify:** AGENTS.md Classify quickly ↔ agent-triage §1 table\n"
    "- [ ] **Card types:** AGENTS.md card types table ↔ each `kanban-*.mdc` ↔ "
    "[kanban-markdown/SKILL.md](../../.cursor/skills/kanban-markdown/SKILL.md) "
    "§ Bug / Inquiry / Commit-issue / Agent cards\n"
    "- [ ] **Handoff:** AGENTS.md End handoff ↔ "
    "[agent-self-evaluation/SKILL.md](../../.cursor/skills/agent-self-evaluation/SKILL.md) "
    "§7 ↔ [agent-self-evaluation.mdc](../../.cursor/rules/agent-self-evaluation.mdc)\n"
    "- [ ] **Failure patterns:** Signatures in rules/triage exist in "
    "[agent-self-evaluation/reference.md](../../.cursor/skills/agent-self-evaluation/reference.md) "
    "or [pre-commit-workflow/reference.md](../../.cursor/skills/pre-commit-workflow/reference.md); "
    "[Consistency matrix](../../.cursor/skills/agent-triage/reference.md) rows still accurate\n"
    "- [ ] **Docs:** [docs/development.md](../../docs/development.md) Cursor agent workflow ↔ "
    "AGENTS.md + consistency links\n"
    "- [ ] **Lessons coverage:** when `.devtool/features/done/` exists, run "
    "`python3 scripts/check_lessons_coverage.py`; composite &lt; 75% should appear as "
    "`Lessons coverage drift alert:` from `check_governance_parity.py`\n"
    "- [ ] **Area table:** AGENTS.md area → skills & rules includes current scoped rules "
    "(`agent-consistency`, `kanban-*`, …)\n"
)

_LABEL_PATHS = """\
- `AGENTS.md`
- `.cursor/rules/agent-routing.mdc`
- `.cursor/skills/agent-triage/SKILL.md`
- `.cursor/skills/agent-triage/reference.md`
- `.cursor/skills/kanban-markdown/SKILL.md`
- `.cursor/rules/kanban-bug-cards.mdc`
- `.cursor/rules/kanban-commit-issue-cards.mdc`
- `.cursor/rules/kanban-inquiry-cards.mdc`
- `.cursor/rules/kanban-agent-cards.mdc`
- `.cursor/skills/agent-self-evaluation/SKILL.md`
- `.cursor/skills/agent-self-evaluation/reference.md`
- `.cursor/skills/pre-commit-workflow/reference.md`
- `docs/development.md`
- `docs/feature-areas.yaml`
"""


def build_governance_audit_body() -> str:
    intro = (
        "Recurring manual audit (suggested **quarterly**). Procedure: "
        "[kanban-markdown/SKILL.md](../../.cursor/skills/kanban-markdown/SKILL.md) "
        "§ Periodic AGENTS.md governance audit. Matrix: "
        "[agent-triage/reference.md](../../.cursor/skills/agent-triage/reference.md) "
        "§ Consistency matrix.\n\n"
        "**Agent:** read-only compare — fill **## Audit findings** below; "
        "do **not** fix drift in this turn unless the user asks."
    )
    return f"""# AGENTS.md governance audit

{intro}

## Audit checklist

{_CHECKLIST}
## Audit findings

_(Agent fills drift bullets here after read-only compare.)_

## Spawned fix cards

| Path | Finding addressed | Status |
| ---- | ----------------- | ------ |
| _(none yet)_ | | |

## Feature Areas

`Agent Workflow`

## Label Paths

{_LABEL_PATHS}
"""


def create_governance_audit_card(
    *,
    audit_date: date | None = None,
    features_dir: Path | None = None,
    force: bool = False,
) -> Path:
    features_dir = features_dir or DEFAULT_FEATURES_DIR
    features_dir.mkdir(parents=True, exist_ok=True)

    audit_date = audit_date or datetime.now(UTC).date()
    date_slug = audit_date.isoformat()
    card_id = f"agents-md-governance-audit-{date_slug}"
    path = features_dir / f"{card_id}.md"

    if path.exists() and not force:
        raise FileExistsError(
            f"Governance audit card already exists: {path}\n"
            "Use --force to overwrite or pass --date YYYY-MM-DD for another id."
        )

    now = datetime.now(UTC)
    created = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    order = _next_order(features_dir)

    frontmatter = f"""---
id: "{card_id}"
status: "todo"
priority: "low"
assignee: null
dueDate: null
created: "{created}"
modified: "{created}"
completedAt: null
labels: []
order: "{order}"
---
"""

    path.write_text(frontmatter + build_governance_audit_body(), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=None,
        metavar="YYYY-MM-DD",
        help="Date slug for card id (default: today UTC)",
    )
    parser.add_argument(
        "--features-dir",
        type=Path,
        default=DEFAULT_FEATURES_DIR,
        help="Kanban features directory (default: .devtool/features)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing card for the same date",
    )
    args = parser.parse_args(argv)

    try:
        path = create_governance_audit_card(
            audit_date=args.date,
            features_dir=args.features_dir,
            force=args.force,
        )
    except FileExistsError as exc:
        print(f"create_governance_audit_card: {exc}", file=sys.stderr)
        return 1

    try:
        display = path.relative_to(REPO_ROOT)
    except ValueError:
        display = path
    print(f"governance audit card created: {display}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
