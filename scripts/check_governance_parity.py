#!/usr/bin/env python3
"""Check governance artifact parity, emit drift alert lines, spawn kanban fix cards."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

AGENTS_MD = REPO_ROOT / "AGENTS.md"
TRIAGE_SKILL = REPO_ROOT / ".cursor/skills/agent-triage/SKILL.md"
FEATURE_AREAS = REPO_ROOT / "docs/feature-areas.yaml"
FEATURES_DIR = REPO_ROOT / ".devtool/features"

SELF_EVAL_SKILL = REPO_ROOT / ".cursor/skills/agent-self-evaluation/SKILL.md"
SELF_EVAL_REFERENCE = REPO_ROOT / ".cursor/skills/agent-self-evaluation/reference.md"
PRE_COMMIT_REFERENCE = REPO_ROOT / ".cursor/skills/pre-commit-workflow/reference.md"
TRIAGE_REFERENCE = REPO_ROOT / ".cursor/skills/agent-triage/reference.md"
LESSONS_INDEX = REPO_ROOT / "docs/lessons-index.yaml"

GOVERNANCE_RULE_GLOBS = (
    ".cursor/rules/agent-*.mdc",
    ".cursor/rules/kanban-*.mdc",
    ".cursor/rules/testing.mdc",
)

PREFIX_ROUTING = "Routing drift alert:"
PREFIX_CARD = "Card-type drift alert:"
PREFIX_FAILURE = "Failure-pattern drift alert:"
PREFIX_REGISTRY = "Registry drift alert:"
PREFIX_LESSONS = "Lessons coverage drift alert:"
PREFIX_COMPACTION = "Compaction drift alert:"
PREFIX_DUPLICATION = "Duplication drift alert:"
PREFIX_FORWARD_FEEDBACK = "Forward feedback audit:"
PREFIX_FORWARD_FEEDBACK_STALE = "Forward feedback stale:"
PREFIX_DOCS_GOVERNANCE_SPLIT = "Docs governance split:"

_STALE_DEV_MD_SECTION_RE = re.compile(
    r"\]\([^)]*development\.md[^)]*\)\s*§|"
    r"(?:docs/)?development\.md\s*§\s*[A-Z]",
)
_DOCS_GOVERNANCE_SPLIT_SIGNATURE = "docs-governance-split"
_DOCS_GOVERNANCE_SCAN_SUFFIXES = frozenset({".md", ".mdc", ".py"})
_DOCS_GOVERNANCE_EXCLUDE_REL = frozenset(
    {
        "docs/forward-feedback-index.yaml",
    }
)

SEVERITY_INFO = "info"
SEVERITY_WARN = "warn"
SEVERITY_CRITICAL = "critical"

DEFAULT_SEVERITY_BY_PREFIX: dict[str, str] = {
    PREFIX_ROUTING: SEVERITY_WARN,
    PREFIX_CARD: SEVERITY_WARN,
    PREFIX_FAILURE: SEVERITY_CRITICAL,
    PREFIX_REGISTRY: SEVERITY_WARN,
    PREFIX_LESSONS: SEVERITY_WARN,
    PREFIX_COMPACTION: SEVERITY_WARN,
    PREFIX_DUPLICATION: SEVERITY_WARN,
}

EPIC_GOVERNANCE_DRIFT = "GovernanceDriftFix"
EPIC_LESSONS_COVERAGE = "LessonsCoverageMetric"
EPIC_AGENT_CONTEXT_BUDGET = "AgentContextBudget"

SEVERITY_PRIORITY: dict[str, str] = {
    SEVERITY_INFO: "low",
    SEVERITY_WARN: "medium",
    SEVERITY_CRITICAL: "high",
}

LABEL_PATHS_BY_PREFIX: dict[str, list[str]] = {
    PREFIX_ROUTING: [
        "AGENTS.md",
        ".cursor/skills/agent-triage/SKILL.md",
        ".cursor/skills/agent-triage/reference.md",
        ".cursor/rules/agent-routing.mdc",
    ],
    PREFIX_CARD: [
        "AGENTS.md",
        ".cursor/skills/kanban-markdown/SKILL.md",
        ".cursor/skills/kanban-markdown/reference.md",
        ".cursor/rules/kanban-card-gates.mdc",
        ".cursor/rules/kanban-feature-cards.mdc",
        ".cursor/rules/kanban-bug-cards.mdc",
        ".cursor/rules/kanban-commit-issue-cards.mdc",
        ".cursor/rules/kanban-inquiry-cards.mdc",
        ".cursor/rules/kanban-plan-cards.mdc",
        ".cursor/rules/kanban-agent-cards.mdc",
    ],
    PREFIX_FAILURE: [
        ".cursor/skills/agent-self-evaluation/reference.md",
        ".cursor/skills/pre-commit-workflow/reference.md",
        ".cursor/rules/agent-consistency.mdc",
        ".cursor/skills/agent-triage/reference.md",
    ],
    PREFIX_REGISTRY: [
        "docs/feature-areas.yaml",
        "AGENTS.md",
        ".cursor/skills/kanban-markdown/SKILL.md",
        ".cursor/skills/kanban-markdown/reference.md",
    ],
    PREFIX_LESSONS: [
        "scripts/check_lessons_coverage.py",
        "scripts/lessons_coverage_lib.py",
        "scripts/check_governance_parity.py",
        "docs/governance/lessons-and-coverage.md",
        ".cursor/skills/agent-triage/reference.md",
    ],
    PREFIX_COMPACTION: [
        "docs/governance/compaction-baseline.yaml",
        "docs/governance/audit-and-compaction.md",
        "scripts/governance_compaction_lib.py",
        "scripts/check_governance_parity.py",
        "AGENTS.md",
    ],
    PREFIX_DUPLICATION: [
        "docs/governance/compaction-baseline.yaml",
        "docs/governance/audit-and-compaction.md",
        "scripts/governance_compaction_lib.py",
        "scripts/check_governance_parity.py",
        ".cursor/skills/kanban-markdown/SKILL.md",
        ".cursor/skills/kanban-markdown/reference.md",
        ".cursor/skills/agent-triage/reference.md",
        "AGENTS.md",
    ],
}

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
_ORDER_RE = re.compile(r'^order:\s*"([^"]+)"', re.MULTILINE)
_STATUS_RE = re.compile(r'^status:\s*"([^"]+)"', re.MULTILINE)
_SEVERITY_PREFIX_RE = re.compile(r"^\[(info|warn|critical)\]\s+")

_TABLE_ROW_RE = re.compile(r"^\|([^|]+)\|", re.MULTILINE)
_SIGNATURE_TABLE_RE = re.compile(r"^\|\s*`([a-z][a-z0-9-]+)`\s*\|", re.MULTILINE)
_SIGNATURE_CITE_RE = re.compile(
    r"(?:signature|§1b grep|grep)\s+`([a-z][a-z0-9-]+)`",
    re.IGNORECASE,
)
_LESSON_ROUTING_SIG_RE = re.compile(r"`([a-z][a-z0-9-]+)`")
_SCHEMA_INTERNAL_PATHS = frozenset(
    {
        "docs/lessons-index.yaml",
        "docs/forward-feedback-index.yaml",
        "docs/governance/README.md",
        "docs/governance/overview.md",
        "docs/governance/kanban-workflow.md",
        "docs/governance/lessons-and-coverage.md",
        "docs/governance/forward-feedback.md",
        "docs/governance/feature-areas-parity.md",
        "docs/governance/audit-and-compaction.md",
        "docs/governance/compaction-baseline.yaml",
        "scripts/build_lessons_index.py",
        "scripts/build_forward_feedback_index.py",
        "scripts/forward_feedback_index_lib.py",
        "scripts/resolve_forward_feedback.py",
        "scripts/batch_forward_feedback_hygiene.py",
        "scripts/resolve_card_tests.py",
        "scripts/pre-commit-pytest.sh",
        "scripts/agent-commit-ready.sh",
        "tests/test_resolve_prior_lessons.py",
        "tests/test_build_lessons_index.py",
        "tests/test_build_forward_feedback_index.py",
        "tests/test_resolve_forward_feedback.py",
        "tests/test_resolve_card_tests.py",
        "scripts/check_lessons_coverage.py",
        "scripts/lessons_coverage_lib.py",
        "scripts/governance_compaction_lib.py",
        "scripts/pre-commit-lessons-coverage.sh",
        "tests/test_check_lessons_coverage.py",
        "tests/test_governance_compaction.py",
    }
)
_LABELS_RE = re.compile(r"^labels:\s*\[(.*?)\]", re.MULTILINE)
_AGENTS_RULE_LINK_RE = re.compile(r"\[([^\]]+)\]\((\.cursor/rules/[a-z0-9_-]+\.mdc)\)")
_AGENTS_SKILL_LINK_RE = re.compile(r"\[([^\]]+)\]\((\.cursor/skills/[^)]+)\)")

_HANDLER_SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*(?:\*)?$")

# Anchor phrases for Classify quickly ↔ triage §1 parity (order matters for messages).
# Baseline artifacts for GovernanceCompact gc0 (Signature: governance-compact-baseline).
GOVERNANCE_COMPACT_BASELINE_GLOBS: tuple[str, ...] = (
    "AGENTS.md",
    ".cursor/rules/agent-routing.mdc",
    ".cursor/skills/agent-triage/SKILL.md",
    ".cursor/skills/agent-triage/reference.md",
    ".cursor/skills/kanban-markdown/SKILL.md",
    ".cursor/skills/kanban-markdown/reference.md",
    ".cursor/skills/agent-self-evaluation/SKILL.md",
    ".cursor/rules/kanban-*.mdc",
    ".cursor/rules/agent-*.mdc",
)

# Named section pairs tracked for duplication (Classify trio; card-type overlap).
DUPLICATION_PAIR_SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("Classify quickly", "AGENTS.md", "## Classify quickly"),
    ("triage §1 Classify", ".cursor/skills/agent-triage/SKILL.md", "## 1. Classify the request"),
    (
        "reference Classify signals",
        ".cursor/skills/agent-triage/reference.md",
        "## Classify the request (signals)",
    ),
    ("AGENTS card types", "AGENTS.md", "### Card types"),
)

_ALWAYS_APPLY_RE = re.compile(r"^alwaysApply:\s*true\b", re.MULTILINE)
_GLOBS_RE = re.compile(r"^globs:\s*(.+)$", re.MULTILINE)

KANBAN_CARD_TYPE_RULE_NAMES: tuple[str, ...] = (
    "kanban-feature-cards.mdc",
    "kanban-bug-cards.mdc",
    "kanban-agent-cards.mdc",
    "kanban-inquiry-cards.mdc",
    "kanban-plan-cards.mdc",
    "kanban-commit-issue-cards.mdc",
    "kanban-feedback-cards.mdc",
)
KANBAN_ALWAYS_ON_RULE = "kanban-card-gates.mdc"

CLASSIFY_ANCHORS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("review card only", ("review card", "review …", "bare `@path`")),
    ("inquire @card", ("Inquire @card", "Inquire …", "kanban-cursor-mode-gates")),
    ("plan @card", ("Plan @card", "Plan …", "Plan Mode")),
    ("plan approved", ("plan approved", "approved", "plan … approved")),
    (
        "agent verb on card",
        (
            "agent verbs",
            "review and update",
            "plan and update",
            "spawn cards from",
        ),
    ),
    ("legacy answer inquiry", ("answer inquiry", "Deprecated", "Inquire")),
    ("card missing label", ("missing", "unknown `labels`", "empty / unknown")),
    ("no card implement", ("without", "a card", "implement / fix")),
    ("inquiry done", ("inquiry", "done", "close only")),
    (
        "bare done multi review",
        ("Done", "QA complete", "card unnamed", "disambiguate", "≥2"),
    ),
    ("epic complete audit", ("epic complete", "run epic audit", "close epic")),
    (
        "archive group complete",
        ("archive group complete", "archive group {name}"),
    ),
    ("governance audit", ("governance audit",)),
    ("explain / audit", ("explain", "is this correct")),
    ("pre-commit failed", ("pre-commit failed",)),
    ("pytest / ruff", ("failing test", "pytest", "ruff / lint")),
    ("ui wiring", ("ui wiring", "dialog")),
    ("agent handoff", ("agent handoff", "process mistake")),
    ("repeated churn", ("repeated mistake", "familiar churn", "churn")),
    ("run tests / commit-ready", ("run tests", "commit-ready", '"run tests"')),
    ("area lesson lookup", ("area lesson lookup", "lessons by area")),
)

REFERENCE_CLASSIFY_HEADING = "## Classify the request (signals)"
AGENTS_CLASSIFY_MAX_ROWS = 5
TRIAGE_CLASSIFY_MAX_ROWS = 0
# Fingerprint of reference § Classify signal first-column cells (normalized).
# Update REFERENCE_CLASSIFY_FINGERPRINT when adding rows (gc9: 594afd85cd2da764).
REFERENCE_CLASSIFY_FINGERPRINT = "594afd85cd2da764"


def _section_after(text: str, heading: str) -> str:
    idx = text.find(heading)
    if idx < 0:
        return ""
    rest = text[idx + len(heading) :]
    next_heading = re.search(r"\n##? ", rest)
    return rest[: next_heading.start()] if next_heading else rest


def _table_first_column(section: str) -> list[str]:
    rows: list[str] = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        if re.match(r"^\|\s*[-:]+", line):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if not cells:
            continue
        head = cells[0].lower().strip("*")
        if head in {"signal", "label"} or head.startswith("-"):
            continue
        rows.append(cells[0])
    return rows


def _contains_anchor(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(phrase.lower() in lowered for phrase in phrases)


def default_severity_for_line(line: str) -> str:
    for prefix, severity in DEFAULT_SEVERITY_BY_PREFIX.items():
        if line.startswith(prefix):
            return severity
    return SEVERITY_WARN


def format_drift_line(line: str, *, severity: str | None = None) -> str:
    """Prefix a drift alert line with [severity] (default from alert type)."""
    if severity is None:
        severity = default_severity_for_line(line)
    bracket = f"[{severity}]"
    if line.startswith(bracket):
        return line
    return f"{bracket} {line}"


def apply_severity(issues: list[str], *, include_severity: bool) -> list[str]:
    if not include_severity:
        return issues
    return [format_drift_line(line) for line in issues]


@dataclass(frozen=True)
class DriftIssue:
    severity: str
    message: str


@dataclass(frozen=True)
class AreaSchemaEntry:
    name: str
    agents_skill: str
    agents_rules: tuple[str, ...]
    lesson_routing_row: str | None
    lesson_signatures: tuple[str, ...]


def parse_drift_line(line: str) -> DriftIssue:
    match = _SEVERITY_PREFIX_RE.match(line)
    if match:
        severity = match.group(1)
        message = line[match.end() :]
    else:
        message = line
        severity = default_severity_for_line(message)
    return DriftIssue(severity=severity, message=message)


def priority_for_severity(severity: str) -> str:
    return SEVERITY_PRIORITY.get(severity, "medium")


def _alert_prefix(message: str) -> str:
    for prefix in DEFAULT_SEVERITY_BY_PREFIX:
        if message.startswith(prefix):
            return prefix
    return PREFIX_ROUTING


def label_paths_for_issue(issue: DriftIssue) -> list[str]:
    return list(
        LABEL_PATHS_BY_PREFIX.get(
            _alert_prefix(issue.message), LABEL_PATHS_BY_PREFIX[PREFIX_ROUTING]
        )
    )


def feature_areas_for_issue(issue: DriftIssue) -> list[str]:
    areas = ["Agent Workflow"]
    if _alert_prefix(issue.message) == PREFIX_REGISTRY:
        areas.append("Feature Area Registry")
    return areas


def corrective_action_for_issue(issue: DriftIssue) -> str:
    prefix = _alert_prefix(issue.message)
    actions = {
        PREFIX_ROUTING: (
            "Restore reference § Classify as canonical per "
            "[agent-triage/reference.md](../../.cursor/skills/agent-triage/reference.md) "
            "§ Classify the request (signals) — Signature: governance-compact-classify-ssot; "
            "AGENTS ≤5-row summary; triage §1 pointer only."
        ),
        PREFIX_CARD: (
            "Align AGENTS.md card types table, `kanban-*.mdc` rules, and "
            "kanban-markdown/SKILL.md sections for the reported label."
        ),
        PREFIX_FAILURE: (
            "Add missing Signature row to the owning `reference.md` or remove the "
            "rule citation — Signature only in `.mdc` files."
        ),
        PREFIX_REGISTRY: (
            "Sync `docs/feature-areas.yaml` governance schema (`agents_skill`, "
            "`agents_rules`, `lesson_routing_row`, `lesson_signatures`) and "
            "**Agent Workflow** `paths` with AGENTS.md area → skills & rules table "
            "(schema-internal lesson paths are excluded); fix `handlers:` duplicates, "
            "malformed symbols, or kanban **Product Methods** symbols missing from the "
            "registry."
        ),
        PREFIX_LESSONS: (
            "Raise Card Done promotion quality (C2 `artifacts:` tails), run the "
            "prior lessons gate on active cards (C3/C4), and re-audit with "
            "`python3 scripts/check_lessons_coverage.py`. See "
            "[docs/governance/lessons-and-coverage.md](../../docs/governance/"
            "lessons-and-coverage.md) § Lessons Coverage Metric."
        ),
        PREFIX_COMPACTION: (
            "Work **AgentContextBudget** epic cards (always-on rule diet, thin AGENTS.md, "
            "index-not-grep); refresh `docs/governance/compaction-baseline.yaml` after "
            "compaction lands. Signature: `governance-compaction-drift-alert`."
        ),
        PREFIX_DUPLICATION: (
            "Reduce duplicated governance prose — Classify trio pointers-only in AGENTS/triage; "
            "move kanban card detail to reference.md; keep scoped `kanban-*.mdc` authoritative. "
            "Refresh `docs/governance/compaction-baseline.yaml` after consolidation. "
            "Signature: `governance-duplication-automation`."
        ),
    }
    return actions.get(prefix, actions[PREFIX_ROUTING])


def card_title_for_issue(issue: DriftIssue) -> str:
    if issue.message.startswith(PREFIX_LESSONS):
        return f"lessons-coverage-drift-{datetime.now(UTC).date().isoformat()}"
    if issue.message.startswith(PREFIX_COMPACTION):
        return f"governance-compaction-advisory-{datetime.now(UTC).date().isoformat()}"
    if issue.message.startswith(PREFIX_DUPLICATION):
        return f"agent-governance-duplication-threshold-{datetime.now(UTC).date().isoformat()}"
    summary = issue.message
    if ":" in summary:
        summary = summary.split(":", 1)[1].strip()
    if len(summary) > 64:
        summary = summary[:61] + "..."
    return f"Governance drift: {summary}"


def _slugify(text: str, *, max_len: int = 36) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].strip("-") or "drift"


def issue_card_id(issue: DriftIssue) -> str:
    if issue.message.startswith(PREFIX_LESSONS):
        return f"lessons-coverage-drift-{datetime.now(UTC).date().isoformat()}"
    if issue.message.startswith(PREFIX_COMPACTION):
        return f"agent-governance-compaction-advisory-{datetime.now(UTC).date().isoformat()}"
    if issue.message.startswith(PREFIX_DUPLICATION):
        return f"agent-governance-duplication-threshold-{datetime.now(UTC).date().isoformat()}"
    group_key = consolidation_group_key(issue.message)
    if group_key is not None:
        return _card_id_for_group_key(group_key)
    digest = hashlib.sha256(issue.message.encode("utf-8")).hexdigest()[:10]
    kind = _slugify(_alert_prefix(issue.message).replace(" drift alert:", ""))
    return f"governance-drift-{kind}-{digest}"


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


def _find_existing_card_for_alert(features_dir: Path, alert_line: str) -> Path | None:
    if not features_dir.is_dir():
        return None
    needle = f"## Alert\n\n{alert_line}"
    for path in features_dir.glob("*.md"):
        if needle in path.read_text(encoding="utf-8"):
            return path
    group_key = consolidation_group_key(alert_line)
    if group_key is not None:
        marker = consolidation_group_marker(group_key)
        card_id = _card_id_for_group_key(group_key)
        for path in features_dir.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            if path.stem == card_id or marker in text:
                return path
    card = _kanban_card_from_registry_label_message(alert_line)
    if card is None:
        return None
    for path in features_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "## Alert" not in text:
            continue
        alert_block = text.split("## Alert", 1)[1].split("\n## ", 1)[0]
        if PREFIX_REGISTRY in alert_block and f"kanban `{card}`" in alert_block:
            return path
    return None


_REGISTRY_METHOD_SINGLE_RE = re.compile(
    rf"^{re.escape(PREFIX_REGISTRY)} kanban `([^`]+)` (?:Product|Label) Methods `([^`]+)` "
    r"missing from feature-areas\.yaml `handlers:`$"
)

_LESSON_SIG_SINGLE_RE = re.compile(
    rf"^{re.escape(PREFIX_REGISTRY)} feature-areas\.yaml \*\*([^*]+)\*\* "
    r"`lesson_signatures` `([^`]+)` — not in lessons-index\.yaml or "
    r"agent-triage reference § Lessons by area / Failure pattern routing$"
)

_LESSON_SIG_GROUP_RE = re.compile(
    rf"^{re.escape(PREFIX_REGISTRY)} feature-areas\.yaml \*\*([^*]+)\*\* — "
    r"`lesson_signatures` missing from lessons-index\.yaml or "
    r"agent-triage reference § Lessons by area / Failure pattern routing:"
)

_AGENTS_PATH_SINGLE_RE = re.compile(
    rf"^{re.escape(PREFIX_REGISTRY)} feature-areas\.yaml lists `([^`]+)` not reflected in "
    r"AGENTS Agent/Kanban area rows$"
)

_AGENTS_PATH_GROUP_MARKER = (
    f"{PREFIX_REGISTRY} feature-areas.yaml paths not reflected in AGENTS Agent/Kanban area rows "
    "(extend `_SCHEMA_INTERNAL_PATHS`)"
)

_HANDLER_DUP_SINGLE_RE = re.compile(
    rf"^{re.escape(PREFIX_REGISTRY)} handler `([^`]+)` listed in both "
    r"\*\*([^*]+)\*\* and \*\*([^*]+)\*\*$"
)

_HANDLER_DUP_GROUP_MARKER = f"{PREFIX_REGISTRY} duplicate `handlers:` across feature areas"


def consolidation_group_key(message: str) -> str | None:
    """Stable spawn group id for consolidated registry drift alerts."""
    if not message.startswith(PREFIX_REGISTRY):
        return None
    card = _kanban_card_from_registry_label_message(message)
    if card and ("Product Methods" in message or "Label Methods" in message):
        return f"registry-label-methods:{card}"
    lesson_single = _LESSON_SIG_SINGLE_RE.match(message)
    if lesson_single:
        return f"lesson-signatures:{lesson_single.group(1)}"
    lesson_group = _LESSON_SIG_GROUP_RE.match(message)
    if lesson_group:
        return f"lesson-signatures:{lesson_group.group(1)}"
    if _AGENTS_PATH_SINGLE_RE.match(message) or message.startswith(_AGENTS_PATH_GROUP_MARKER):
        return "schema-internal-agents-paths"
    if _HANDLER_DUP_SINGLE_RE.match(message) or message.startswith(_HANDLER_DUP_GROUP_MARKER):
        return "handler-duplicates"
    return None


def consolidation_group_marker(group_key: str) -> str:
    """Substring for deduping open cards by consolidation group."""
    if group_key.startswith("lesson-signatures:"):
        area = group_key.split(":", 1)[1]
        return f"feature-areas.yaml **{area}** — `lesson_signatures` missing"
    if group_key == "schema-internal-agents-paths":
        return _AGENTS_PATH_GROUP_MARKER
    if group_key == "handler-duplicates":
        return _HANDLER_DUP_GROUP_MARKER
    if group_key.startswith("registry-label-methods:"):
        card = group_key.split(":", 1)[1]
        return f"kanban `{card}` — Product Methods symbols"
    return group_key


def _card_id_for_group_key(group_key: str) -> str:
    digest = hashlib.sha256(group_key.encode("utf-8")).hexdigest()[:10]
    return f"governance-drift-registry-{digest}"


def _kanban_card_from_registry_label_message(message: str) -> str | None:
    if not message.startswith(PREFIX_REGISTRY):
        return None
    single = _REGISTRY_METHOD_SINGLE_RE.match(message)
    if single:
        return single.group(1)
    grouped = re.match(
        rf"^{re.escape(PREFIX_REGISTRY)} kanban `([^`]+)` — (?:Product|Label) Methods symbols "
        r"missing from feature-areas\.yaml `handlers:`",
        message,
    )
    return grouped.group(1) if grouped else None


def consolidate_drift_issues_for_spawn(issues: list[str]) -> list[str]:
    """Merge registry drift alerts by root cause before spawning kanban cards."""
    registry_by_card: dict[str, list[tuple[str, str]]] = {}
    lesson_sigs_by_area: dict[str, list[tuple[str, str]]] = {}
    agents_paths: list[tuple[str, str]] = []
    handler_dups: list[tuple[str, str, str, str]] = []
    passthrough: list[str] = []

    for line in issues:
        issue = parse_drift_line(line)
        message = issue.message
        single_method = _REGISTRY_METHOD_SINGLE_RE.match(message)
        if single_method:
            card_name, symbol = single_method.group(1), single_method.group(2)
            registry_by_card.setdefault(card_name, []).append((line, symbol))
            continue
        lesson_match = _LESSON_SIG_SINGLE_RE.match(message)
        if lesson_match:
            area_name, sig = lesson_match.group(1), lesson_match.group(2)
            lesson_sigs_by_area.setdefault(area_name, []).append((line, sig))
            continue
        agents_match = _AGENTS_PATH_SINGLE_RE.match(message)
        if agents_match:
            agents_paths.append((line, agents_match.group(1)))
            continue
        handler_match = _HANDLER_DUP_SINGLE_RE.match(message)
        if handler_match:
            handler_dups.append(
                (line, handler_match.group(1), handler_match.group(2), handler_match.group(3))
            )
            continue
        passthrough.append(line)

    merged: list[str] = list(passthrough)

    for card_name in sorted(registry_by_card):
        entries = registry_by_card[card_name]
        if len(entries) == 1:
            merged.append(entries[0][0])
            continue
        symbols = sorted({symbol for _line, symbol in entries})
        quoted = ", ".join(f"`{symbol}`" for symbol in symbols)
        body = (
            f"{PREFIX_REGISTRY} kanban `{card_name}` — Product Methods symbols "
            f"missing from feature-areas.yaml `handlers:`: {quoted}"
        )
        severity = parse_drift_line(entries[0][0]).severity
        merged.append(format_drift_line(body, severity=severity))

    for area_name in sorted(lesson_sigs_by_area):
        entries = lesson_sigs_by_area[area_name]
        if len(entries) == 1:
            merged.append(entries[0][0])
            continue
        sigs = sorted({sig for _line, sig in entries})
        quoted = ", ".join(f"`{sig}`" for sig in sigs)
        body = (
            f"{PREFIX_REGISTRY} feature-areas.yaml **{area_name}** — "
            "`lesson_signatures` missing from lessons-index.yaml or "
            "agent-triage reference § Lessons by area / Failure pattern routing: "
            f"{quoted}"
        )
        severity = parse_drift_line(entries[0][0]).severity
        merged.append(format_drift_line(body, severity=severity))

    if len(agents_paths) == 1:
        merged.append(agents_paths[0][0])
    elif len(agents_paths) > 1:
        paths = sorted({path for _line, path in agents_paths})
        quoted = ", ".join(f"`{path}`" for path in paths)
        body = f"{_AGENTS_PATH_GROUP_MARKER}: {quoted}"
        severity = parse_drift_line(agents_paths[0][0]).severity
        merged.append(format_drift_line(body, severity=severity))

    if len(handler_dups) == 1:
        merged.append(handler_dups[0][0])
    elif len(handler_dups) > 1:
        parts = sorted(
            {
                f"`{handler}` in **{area_a}** and **{area_b}**"
                for _line, handler, area_a, area_b in handler_dups
            }
        )
        body = f"{_HANDLER_DUP_GROUP_MARKER} — " + "; ".join(parts)
        severity = parse_drift_line(handler_dups[0][0]).severity
        merged.append(format_drift_line(body, severity=severity))

    return merged


def card_label_for_issue(issue: DriftIssue) -> str:
    if issue.message.startswith(PREFIX_LESSONS):
        return "agent"
    return "feature"


_SPAWN_TBD_PRODUCT_METHODS = "- _TBD — agent fills at pre-implementation review._"
_SPAWN_TBD_DECISIONS = "- _TBD — fill after prior lessons gate and card-type review._"
_SPAWN_PRIOR_LESSONS_STUB = (
    "**Prior lessons (YYYY-MM-DD):** Review `docs/lessons-index.yaml` **Agent Workflow** "
    "block; run `python3 scripts/resolve_prior_lessons.py` with this card's epic, "
    "Feature Area, and Product Paths; cite done-card stems, Signatures, or paths before "
    "`in-progress`."
)
_SPAWN_TBD_AC = "- [ ] _TBD_"
_SPAWN_TBD_TESTS_FILES = "- _TBD_"
_SPAWN_TBD_TESTS_METHODS = "- _TBD_"
_SPAWN_TBD_TESTS_VERIFY = (
    "- _TBD — `scripts/pre-commit-pytest.sh` on staged paths (authoritative scope)._"
)
_SPAWN_TBD_DOCS = "- _TBD_"

_SPAWN_TESTS_DOCS_BLOCK = f"""## Tests

### Files

{_SPAWN_TBD_TESTS_FILES}

### Methods

{_SPAWN_TBD_TESTS_METHODS}

### Verify (agent)

{_SPAWN_TBD_TESTS_VERIFY}

## Docs

{_SPAWN_TBD_DOCS}
"""


def _spawn_review_sections(label: str, issue: DriftIssue) -> str:
    """Label-type sections required before in-progress — placeholders when auto-spawned."""
    decisions = _SPAWN_TBD_DECISIONS
    if label == "agent" and issue.message.startswith(PREFIX_LESSONS):
        decisions = f"- {_SPAWN_PRIOR_LESSONS_STUB}"
    tail = f"""## Product Methods

{_SPAWN_TBD_PRODUCT_METHODS}

{_SPAWN_TESTS_DOCS_BLOCK}

## Decisions

{decisions}

## Acceptance Criteria

{_SPAWN_TBD_AC}
"""
    if label == "agent":
        description = corrective_action_for_issue(issue)
        if issue.message.startswith(PREFIX_LESSONS):
            description += (
                " **C4:** active cards with surfaced lessons need "
                "`**Prior lessons (YYYY-MM-DD):**` cites — "
                "[kanban-prior-lessons-gate.mdc](../../.cursor/rules/kanban-prior-lessons-gate.mdc)."
            )
        return f"""## Description

{description}

## Feature Area

`Agent Workflow`

{tail}"""
    return tail


def build_drift_card_body(issue: DriftIssue) -> str:
    label_paths = label_paths_for_issue(issue)
    feature_areas = feature_areas_for_issue(issue)
    title = card_title_for_issue(issue)
    paths_md = "\n".join(f"- `{path}`" for path in label_paths)
    areas_md = "\n".join(f"`{area}`" for area in feature_areas)
    label = card_label_for_issue(issue)
    if issue.message.startswith(PREFIX_LESSONS):
        spawned = (
            f"Spawned by `scripts/check_governance_parity.py` (epic **{EPIC_LESSONS_COVERAGE}**)."
        )
    else:
        spawned = (
            f"Spawned by `scripts/check_governance_parity.py` (epic **{EPIC_GOVERNANCE_DRIFT}**)."
        )
    review = _spawn_review_sections(label, issue)
    if label == "agent":
        return f"""# {title}

{spawned}

## Alert

{issue.message}

## Product Paths

{paths_md}

{review}"""
    return f"""# {title}

{spawned}

## Alert

{issue.message}

## Feature Areas

{areas_md}

## Product Paths

{paths_md}

{review}"""


def create_drift_alert_cards(
    issues: list[str],
    *,
    features_dir: Path,
) -> list[Path]:
    """Create todo kanban cards for drift issues; skip duplicates by ## Alert text."""
    features_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    for line in consolidate_drift_issues_for_spawn(issues):
        issue = parse_drift_line(line)
        if issue.message.startswith(PREFIX_COMPACTION) and issue.severity != SEVERITY_CRITICAL:
            continue
        existing = _find_existing_card_for_alert(features_dir, issue.message)
        if existing is not None:
            continue

        card_id = issue_card_id(issue)
        path = features_dir / f"{card_id}.md"
        if path.exists():
            continue

        priority = priority_for_severity(issue.severity)
        order = _next_order(features_dir)
        epic = (
            EPIC_LESSONS_COVERAGE
            if issue.message.startswith(PREFIX_LESSONS)
            else EPIC_AGENT_CONTEXT_BUDGET
            if issue.message.startswith(PREFIX_COMPACTION)
            or issue.message.startswith(PREFIX_DUPLICATION)
            else EPIC_GOVERNANCE_DRIFT
        )
        labels = (
            '["agent"]'
            if issue.message.startswith(PREFIX_LESSONS)
            or issue.message.startswith(PREFIX_COMPACTION)
            or issue.message.startswith(PREFIX_DUPLICATION)
            else '["feature"]'
        )
        frontmatter = f"""---
id: "{card_id}"
status: "todo"
priority: "{priority}"
assignee: null
epic: "{epic}"
dueDate: null
created: "{now}"
modified: "{now}"
completedAt: null
labels: {labels}
order: "{order}"
---
"""
        path.write_text(frontmatter + build_drift_card_body(issue), encoding="utf-8")
        created.append(path)

    return created


def _agents_classify_section(text: str) -> str:
    section = _section_after(text, "## Classify quickly")
    for marker in ("\n### Card types", "\n## Area"):
        idx = section.find(marker)
        if idx >= 0:
            section = section[:idx]
    next_h2 = re.search(r"\n## ", section)
    if next_h2:
        section = section[: next_h2.start()]
    return section


def _classify_signals_section(text: str) -> str:
    section = _section_after(text, REFERENCE_CLASSIFY_HEADING)
    task_idx = section.find("### Task types")
    if task_idx >= 0:
        section = section[:task_idx]
    return section


def _classify_signal_fingerprint(rows: list[str]) -> str:
    normalized = [re.sub(r"\*\*", "", row).strip().lower() for row in rows]
    digest = hashlib.sha256("\n".join(normalized).encode()).hexdigest()
    return digest[:16]


_HANDOFF_FIELD_LINE_RE = re.compile(r"^-\s+\*\*")
_HANDOFF_DUP_MIN_RUN = 3


def _handoff_field_lines(text: str) -> list[str]:
    return [
        line.strip() for line in text.splitlines() if _HANDOFF_FIELD_LINE_RE.match(line.strip())
    ]


def extract_skill_handoff_template_lines(skill_text: str) -> list[str]:
    """Compact §7 Self-evaluation field lines from the canonical fenced template."""
    section = _section_after(skill_text, "## 7. Handoff format")
    compact_idx = section.find("### Self-evaluation (compact")
    if compact_idx < 0:
        return []
    rest = section[compact_idx:]
    fence = re.search(r"```markdown\n(.*?)```", rest, re.DOTALL)
    if not fence:
        return []
    return _handoff_field_lines(fence.group(1))


def extract_agents_end_handoff_field_lines(agents_text: str) -> list[str]:
    """`- **Field:**` lines under AGENTS ``## End handoff``."""
    section = _section_after(agents_text, "## End handoff")
    return _handoff_field_lines(section)


def find_handoff_template_duplication_run(
    candidate_lines: list[str],
    template_lines: list[str],
    *,
    min_run: int = _HANDOFF_DUP_MIN_RUN,
) -> list[str] | None:
    """Return the first matching consecutive run (≥ min_run lines)."""
    if len(template_lines) < min_run or len(candidate_lines) < min_run:
        return None
    for start in range(len(candidate_lines) - min_run + 1):
        chunk = candidate_lines[start : start + min_run]
        for template_start in range(len(template_lines) - min_run + 1):
            if chunk == template_lines[template_start : template_start + min_run]:
                return chunk
    return None


def check_handoff_duplication_pair(agents_text: str, skill_text: str) -> list[str]:
    """Detect gc4 regression — AGENTS End handoff repeats SKILL §7 compact fields."""
    template = extract_skill_handoff_template_lines(skill_text)
    agents_fields = extract_agents_end_handoff_field_lines(agents_text)
    chunk = find_handoff_template_duplication_run(agents_fields, template)
    if chunk is None:
        return []
    sample = chunk[0][:60]
    return [
        f"{PREFIX_ROUTING} AGENTS End handoff duplicates SKILL §7 compact template "
        f"({len(chunk)} consecutive field lines) — restore pointer-only gc4 handoff; "
        f"Signature: governance-gc7-handoff-duplication-pair — starts: {sample}…"
    ]


def check_classify_parity(
    agents_text: str,
    triage_text: str,
    reference_text: str,
) -> list[str]:
    ref_section = _classify_signals_section(reference_text)
    agents_section = _agents_classify_section(agents_text)
    triage_section = _section_after(triage_text, "## 1. Classify the request")
    issues: list[str] = []

    ref_rows = _table_first_column(ref_section)
    if not ref_rows:
        issues.append(
            f"{PREFIX_ROUTING} reference § Classify has no signal rows — "
            f"restore {REFERENCE_CLASSIFY_HEADING}"
        )
    else:
        fingerprint = _classify_signal_fingerprint(ref_rows)
        if fingerprint != REFERENCE_CLASSIFY_FINGERPRINT:
            issues.append(
                f"{PREFIX_ROUTING} reference § Classify fingerprint drift "
                f"(got {fingerprint}, expected {REFERENCE_CLASSIFY_FINGERPRINT}) — "
                f"{len(ref_rows)} signal rows; update REFERENCE_CLASSIFY_FINGERPRINT "
                f"when intentional"
            )

    for name, phrases in CLASSIFY_ANCHORS:
        if ref_section and not _contains_anchor(ref_section, phrases):
            issues.append(
                f'{PREFIX_ROUTING} reference Classify row "{name}" missing '
                f"(anchor phrases: {', '.join(phrases[:2])}…)"
            )

    agents_rows = _table_first_column(agents_section)
    if len(agents_rows) > AGENTS_CLASSIFY_MAX_ROWS:
        issues.append(
            f"{PREFIX_ROUTING} AGENTS Classify quickly has {len(agents_rows)} rows "
            f"(max {AGENTS_CLASSIFY_MAX_ROWS}) — move signals to reference § Classify only"
        )

    triage_rows = _table_first_column(triage_section)
    if len(triage_rows) > TRIAGE_CLASSIFY_MAX_ROWS:
        issues.append(
            f"{PREFIX_ROUTING} triage §1 has {len(triage_rows)} Classify table rows "
            f"(max {TRIAGE_CLASSIFY_MAX_ROWS}) — link reference § Classify only "
            f"(Signature: governance-compact-classify-ssot)"
        )

    return issues


def extract_reference_signatures(*reference_paths: Path) -> set[str]:
    signatures: set[str] = set()
    for path in reference_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        signatures.update(_SIGNATURE_TABLE_RE.findall(text))
    return signatures


def extract_rule_signature_cites(rule_paths: list[Path]) -> set[str]:
    cites: set[str] = set()
    for path in rule_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        cites.update(_SIGNATURE_CITE_RE.findall(text))
    return cites


def check_failure_pattern_parity(
    reference_signatures: set[str],
    rule_cites: set[str],
) -> list[str]:
    issues: list[str] = []
    for sig in sorted(rule_cites):
        if sig not in reference_signatures:
            issues.append(
                f"{PREFIX_FAILURE} Rule cites `{sig}` — no row in self-eval or pre-commit reference"
            )
    return issues


def _normalize_path(path: str) -> str:
    path = path.strip().rstrip("/")
    if path.endswith(".mdc") or path.endswith(".md"):
        return path
    if not path.endswith("/") and "." not in Path(path).name:
        return path + "/"
    return path


def _rule_file_from_entry(entry: str) -> str:
    return entry.split("#", 1)[0].strip()


def is_schema_internal_registry_path(path: str) -> bool:
    """Agent Workflow paths validated by schema keys, not AGENTS area rows."""
    normalized = path.strip().rstrip("/")
    if normalized in _SCHEMA_INTERNAL_PATHS:
        return True
    name = Path(normalized).name
    return normalized.startswith("scripts/resolve_") and name.endswith(".py")


def load_area_schema_entries(feature_areas_text: str) -> list[AreaSchemaEntry]:
    """Areas with agents_skill set — mechanical governance schema parity."""
    if yaml is None:
        raise RuntimeError("PyYAML required — install project dependencies")
    data = yaml.safe_load(feature_areas_text)
    areas = data.get("areas", {})
    entries: list[AreaSchemaEntry] = []
    for name, entry in areas.items():
        if not isinstance(entry, dict):
            continue
        skill = entry.get("agents_skill")
        if not skill:
            continue
        raw_rules = entry.get("agents_rules", []) or []
        raw_sigs = entry.get("lesson_signatures", []) or []
        routing_row = entry.get("lesson_routing_row")
        entries.append(
            AreaSchemaEntry(
                name=str(name),
                agents_skill=str(skill).strip(),
                agents_rules=tuple(str(rule).strip() for rule in raw_rules if str(rule).strip()),
                lesson_routing_row=(str(routing_row).strip() if routing_row is not None else None),
                lesson_signatures=tuple(str(sig).strip() for sig in raw_sigs if str(sig).strip()),
            )
        )
    return entries


def extract_lessons_by_area_first_column(reference_text: str) -> list[str]:
    section = _section_after(reference_text, "## Lessons by area")
    return _table_first_column(section)


def extract_lesson_routing_reference_signatures(reference_text: str) -> set[str]:
    """Signatures cited in triage § Lessons by area and § Failure pattern routing."""
    lessons_section = _section_after(reference_text, "## Lessons by area")
    failure_section = _section_after(reference_text, "## Failure pattern routing")
    signatures: set[str] = set()
    for section in (lessons_section, failure_section):
        for match in _LESSON_ROUTING_SIG_RE.finditer(section):
            token = match.group(1)
            if token.islower() and "-" in token:
                signatures.add(token)
    return signatures


def extract_lessons_index_area_signatures(lessons_index_text: str, area_name: str) -> set[str]:
    if yaml is None:
        raise RuntimeError("PyYAML required — install project dependencies")
    data = yaml.safe_load(lessons_index_text)
    area_block = data.get("areas", {}).get(area_name, {})
    raw = area_block.get("signatures", []) or []
    return {
        str(sig).strip() for sig in raw if str(sig).strip() and str(sig).strip() not in {"…", "..."}
    }


def check_area_schema_parity(
    repo_root: Path,
    schema_entries: list[AreaSchemaEntry],
    triage_reference_text: str,
    lessons_index_text: str,
    reference_signatures: set[str],
) -> list[str]:
    """Mechanical checks for governance area schema keys (agents_skill areas)."""
    issues: list[str] = []
    routing_rows = extract_lessons_by_area_first_column(triage_reference_text)
    routing_reference_sigs = extract_lesson_routing_reference_signatures(triage_reference_text)
    lesson_index_sigs_by_area = {
        entry.name: extract_lessons_index_area_signatures(lessons_index_text, entry.name)
        for entry in schema_entries
    }

    for entry in schema_entries:
        skill_path = repo_root / ".cursor/skills" / entry.agents_skill / "SKILL.md"
        if not skill_path.is_file():
            issues.append(
                f"{PREFIX_REGISTRY} feature-areas.yaml **{entry.name}** `agents_skill` "
                f"`{entry.agents_skill}` — missing `{skill_path.relative_to(repo_root)}`"
            )

        for rule_entry in entry.agents_rules:
            rule_file = _rule_file_from_entry(rule_entry)
            rule_path = repo_root / ".cursor/rules" / rule_file
            if not rule_path.is_file():
                issues.append(
                    f"{PREFIX_REGISTRY} feature-areas.yaml **{entry.name}** `agents_rules` "
                    f"entry `{rule_entry}` — missing `.cursor/rules/{rule_file}`"
                )

        if entry.lesson_routing_row:
            needle = entry.lesson_routing_row.lower()
            if not any(needle in row.lower() for row in routing_rows):
                issues.append(
                    f"{PREFIX_REGISTRY} feature-areas.yaml **{entry.name}** "
                    f"`lesson_routing_row` `{entry.lesson_routing_row}` — no match in "
                    "agent-triage/reference.md § Lessons by area"
                )

        for sig in entry.lesson_signatures:
            in_index = sig in lesson_index_sigs_by_area.get(entry.name, set())
            in_reference = sig in routing_reference_sigs or sig in reference_signatures
            if not in_index and not in_reference:
                issues.append(
                    f"{PREFIX_REGISTRY} feature-areas.yaml **{entry.name}** "
                    f"`lesson_signatures` `{sig}` — not in lessons-index.yaml or "
                    "agent-triage reference § Lessons by area / Failure pattern routing"
                )

    return issues


def load_agent_workflow_paths(feature_areas_text: str) -> set[str]:
    if yaml is None:
        raise RuntimeError("PyYAML required — install project dependencies")
    data = yaml.safe_load(feature_areas_text)
    area = data.get("areas", {}).get("Agent Workflow", {})
    paths = area.get("paths", []) or []
    return {_normalize_path(str(p)) for p in paths}


def load_area_handlers(feature_areas_text: str) -> dict[str, list[str]]:
    """Return feature area label → handlers list from docs/feature-areas.yaml."""
    if yaml is None:
        raise RuntimeError("PyYAML required — install project dependencies")
    data = yaml.safe_load(feature_areas_text)
    areas = data.get("areas", {})
    result: dict[str, list[str]] = {}
    for name, entry in areas.items():
        if not isinstance(entry, dict):
            continue
        raw = entry.get("handlers", []) or []
        if raw:
            result[str(name)] = [str(handler).strip() for handler in raw]
    return result


def is_valid_handler_symbol(symbol: str) -> bool:
    """True for registry-style handler symbols (not repo file paths)."""
    token = symbol.strip()
    if not token or "/" in token or " " in token or token.endswith(".py"):
        return False
    return bool(_HANDLER_SYMBOL_RE.match(token))


def check_handlers_registry_parity(handlers_by_area: dict[str, list[str]]) -> list[str]:
    """Malformed handler lines and duplicate symbols across feature areas."""
    issues: list[str] = []
    seen: dict[str, str] = {}

    for area_name, handlers in sorted(handlers_by_area.items()):
        for handler in handlers:
            if not handler:
                issues.append(
                    f"{PREFIX_REGISTRY} feature-areas.yaml **{area_name}** has empty "
                    "`handlers:` entry"
                )
                continue
            if not is_valid_handler_symbol(handler):
                issues.append(
                    f"{PREFIX_REGISTRY} feature-areas.yaml **{area_name}** has malformed "
                    f"handler `{handler}`"
                )
                continue
            previous = seen.get(handler)
            if previous is not None and previous != area_name:
                issues.append(
                    f"{PREFIX_REGISTRY} handler `{handler}` listed in both "
                    f"**{previous}** and **{area_name}**"
                )
            else:
                seen[handler] = area_name

    return issues


def _handler_symbols_from_label_methods_section(section: str) -> set[str]:
    symbols: set[str] = set()
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        payload = stripped.lstrip("- ").strip()
        if "—" in payload:
            payload = payload.split("—", 1)[1].strip()
        elif " - " in payload:
            payload = payload.split(" - ", 1)[1].strip()

        backtick_tokens = re.findall(r"`([^`]+)`", payload)
        if backtick_tokens:
            for token in backtick_tokens:
                if is_valid_handler_symbol(token):
                    symbols.add(token)
            continue

        bare = payload.strip("`").strip()
        if is_valid_handler_symbol(bare):
            symbols.add(bare)
    return symbols


def extract_label_method_symbols(card_text: str) -> set[str]:
    symbols: set[str] = set()
    for heading in ("## Product Methods", "## Label Methods"):
        section = _section_after(card_text, heading)
        if section.strip():
            symbols.update(_handler_symbols_from_label_methods_section(section))
    return symbols


def extract_feature_areas_from_card(card_text: str) -> set[str]:
    section = _section_after(card_text, "## Feature Areas")
    if not section.strip():
        return set()
    return {match.group(1).strip() for match in re.finditer(r"`([^`]+)`", section)}


def _registry_handler_set(handlers_by_area: dict[str, list[str]]) -> set[str]:
    symbols: set[str] = set()
    for handlers in handlers_by_area.values():
        symbols.update(handlers)
    return symbols


def check_kanban_label_methods_handlers(
    features_dir: Path,
    handlers_by_area: dict[str, list[str]],
) -> list[str]:
    """Product Methods symbols on open cards must exist in feature-areas.yaml handlers."""
    if not features_dir.is_dir():
        return []

    registry_handlers = _registry_handler_set(handlers_by_area)
    issues: list[str] = []

    for path in sorted(features_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        status, _order = _read_frontmatter(path)
        if status not in {"todo", "in-progress", "review"}:
            continue

        feature_areas = extract_feature_areas_from_card(text)
        symbols = extract_label_method_symbols(text)
        if not feature_areas or not symbols:
            continue

        for symbol in sorted(symbols):
            if symbol not in registry_handlers:
                issues.append(
                    f"{PREFIX_REGISTRY} kanban `{path.name}` Product Methods `{symbol}` "
                    "missing from feature-areas.yaml `handlers:`"
                )

    return issues


def _skill_link_to_path(link: str) -> str:
    if link.endswith("/SKILL.md"):
        return link[: -len("SKILL.md")]
    return _normalize_path(link)


def extract_agents_governance_paths(
    agents_text: str,
    schema_entries: list[AreaSchemaEntry] | None = None,
) -> set[str]:
    from scripts.sync_agents_area_table import row_matches_area

    section = _section_after(agents_text, "## Area → skills & rules")
    paths: set[str] = {"AGENTS.md"}
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        if re.match(r"^\|\s*[-:]+", line):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if not cells or cells[0].lower().strip("*") in {"area", "label"}:
            continue
        if schema_entries is not None and not any(
            row_matches_area(cells[0], entry) for entry in schema_entries
        ):
            continue
        for _name, rule_path in _AGENTS_RULE_LINK_RE.findall(line):
            paths.add(_normalize_path(rule_path))
        for _name, skill_path in _AGENTS_SKILL_LINK_RE.findall(line):
            paths.add(_skill_link_to_path(skill_path))
    return paths


def filter_registry_compare_paths(paths: set[str]) -> set[str]:
    """Drop schema-internal Agent Workflow paths — covered by check_area_schema_parity."""
    return {path for path in paths if not is_schema_internal_registry_path(path)}


def check_registry_parity(
    yaml_paths: set[str],
    agents_paths: set[str],
) -> list[str]:
    """Compare Agent Workflow skill/doc paths with AGENTS workflow row links.

    Rule files (`.mdc`) are verified by ``check_agents_area_table_parity`` — excluded here.
    """
    yaml_compare = filter_registry_compare_paths(
        {path for path in yaml_paths if not path.endswith(".mdc")}
    )
    agents_compare = {path for path in agents_paths if not path.endswith(".mdc")}
    issues: list[str] = []
    for path in sorted(yaml_compare - agents_compare):
        issues.append(
            f"{PREFIX_REGISTRY} feature-areas.yaml lists `{path}` not reflected in "
            "AGENTS Agent/Kanban area rows"
        )
    for path in sorted(agents_compare - yaml_compare):
        if path == "AGENTS.md":
            continue
        issues.append(
            f"{PREFIX_REGISTRY} AGENTS area table lists `{path}` missing from "
            "feature-areas.yaml Agent Workflow paths"
        )
    return issues


def _parse_labels_from_frontmatter(text: str) -> set[str]:
    match = _LABELS_RE.search(text)
    if not match:
        return set()
    inner = match.group(1)
    return {
        label.strip().strip('"').strip("'").lower() for label in inner.split(",") if label.strip()
    }


def collect_feature_card_labels(features_dir: Path) -> set[str]:
    labels: set[str] = set()
    if not features_dir.is_dir():
        return labels
    for pattern in ("*.md", "done/*.md", "archived/*.md"):
        for path in features_dir.glob(pattern):
            labels.update(_parse_labels_from_frontmatter(path.read_text(encoding="utf-8")))
    return labels


def parse_agents_card_type_labels(agents_text: str) -> set[str]:
    section = _section_after(agents_text, "### Card types")
    labels: set[str] = set()
    for row in _table_first_column(section):
        for match in re.finditer(r"`([a-z][a-z0-9-]*)`", row):
            labels.add(match.group(1))
    return labels


def check_card_type_parity(
    card_labels: set[str],
    agents_labels: set[str],
) -> list[str]:
    issues: list[str] = []
    for label in sorted(card_labels):
        if label not in agents_labels:
            issues.append(
                f"{PREFIX_CARD} Frontmatter label `{label}` on card — add AGENTS "
                "card types row + kanban rule"
            )
    return issues


def check_kanban_rule_globs(repo_root: Path) -> list[str]:
    """gc3 — card-type kanban rules scoped; kanban-card-gates always-on."""
    issues: list[str] = []
    rules_dir = repo_root / ".cursor/rules"
    gates_path = rules_dir / KANBAN_ALWAYS_ON_RULE
    if gates_path.is_file():
        gates_text = gates_path.read_text(encoding="utf-8")
        if not _ALWAYS_APPLY_RE.search(gates_text):
            issues.append(
                f"{PREFIX_ROUTING} `{KANBAN_ALWAYS_ON_RULE}` must have "
                "`alwaysApply: true` (kanban label + prompt verb gate)"
            )
        if _GLOBS_RE.search(gates_text):
            issues.append(
                f"{PREFIX_ROUTING} `{KANBAN_ALWAYS_ON_RULE}` must not use `globs` when always-on"
            )
    else:
        issues.append(f"{PREFIX_ROUTING} missing always-on rule `{KANBAN_ALWAYS_ON_RULE}`")

    for name in KANBAN_CARD_TYPE_RULE_NAMES:
        path = rules_dir / name
        if not path.is_file():
            issues.append(f"{PREFIX_ROUTING} missing scoped kanban rule `{name}`")
            continue
        text = path.read_text(encoding="utf-8")
        if _ALWAYS_APPLY_RE.search(text):
            issues.append(
                f"{PREFIX_ROUTING} `{name}` must not have `alwaysApply: true` — "
                "scope with `.devtool/features/**` globs (gc3)"
            )
        globs_match = _GLOBS_RE.search(text)
        if not globs_match or ".devtool/features" not in globs_match.group(1):
            issues.append(
                f"{PREFIX_ROUTING} `{name}` must set `globs` under `.devtool/features/**`"
            )
    return issues


INDEX_NOT_GREP_SIGNATURE = "governance-index-not-grep"

INDEX_NOT_GREP_REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    ".cursor/rules/kanban-prior-lessons-gate.mdc": (
        INDEX_NOT_GREP_SIGNATURE,
        "lessons-index.yaml",
        "resolve_prior_lessons.py",
    ),
    ".cursor/skills/agent-triage/SKILL.md": (
        INDEX_NOT_GREP_SIGNATURE,
        "lessons-index.yaml",
        "resolve_prior_lessons.py",
    ),
    "docs/governance/lessons-and-coverage.md": (
        INDEX_NOT_GREP_SIGNATURE,
        "resolve_prior_lessons.py",
    ),
}


def check_index_not_grep_routing(repo_root: Path) -> list[str]:
    """acb4 — yaml/index before broad done/archived folder grep."""
    issues: list[str] = []
    for rel, tokens in INDEX_NOT_GREP_REQUIRED_TOKENS.items():
        path = repo_root / rel
        if not path.is_file():
            issues.append(f"{PREFIX_ROUTING} missing index-not-grep artifact `{rel}`")
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                issues.append(
                    f"{PREFIX_ROUTING} `{rel}` missing index-not-grep token "
                    f"`{token}` — Signature: {INDEX_NOT_GREP_SIGNATURE}"
                )
    ref = repo_root / ".cursor/skills/kanban-markdown/reference.md"
    if not ref.is_file():
        issues.append(
            f"{PREFIX_ROUTING} missing kanban-markdown/reference.md for "
            f"index-not-grep — Signature: {INDEX_NOT_GREP_SIGNATURE}"
        )
    else:
        ref_text = ref.read_text(encoding="utf-8")
        if "Index vs folder grep" not in ref_text:
            issues.append(
                f"{PREFIX_ROUTING} kanban-markdown/reference.md missing "
                f"§ Index vs folder grep — Signature: {INDEX_NOT_GREP_SIGNATURE}"
            )
        if INDEX_NOT_GREP_SIGNATURE not in ref_text:
            issues.append(
                f"{PREFIX_ROUTING} kanban-markdown/reference.md missing "
                f"Signature `{INDEX_NOT_GREP_SIGNATURE}`"
            )
    return issues


DISCOVERY_LADDER_SIGNATURE = "governance-discovery-ladder"

DISCOVERY_LADDER_BRANCH_TOKENS: tuple[str, ...] = (
    "Governance",
    "Kanban",
    "Docs-only",
    "Product",
    "Failure",
)

DISCOVERY_LADDER_REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    ".cursor/rules/agent-routing.mdc": (
        "Discovery ladder",
        DISCOVERY_LADDER_SIGNATURE,
    ),
    ".cursor/skills/agent-triage/SKILL.md": (
        "Discovery ladder",
        DISCOVERY_LADDER_SIGNATURE,
    ),
}


def check_discovery_ladder_routing(repo_root: Path) -> list[str]:
    """acb5 — classify → area → grep decision ladder SSOT in reference."""
    issues: list[str] = []
    ref = repo_root / ".cursor/skills/agent-triage/reference.md"
    if not ref.is_file():
        issues.append(
            f"{PREFIX_ROUTING} missing agent-triage/reference.md for "
            f"discovery ladder — Signature: {DISCOVERY_LADDER_SIGNATURE}"
        )
        return issues
    ref_text = ref.read_text(encoding="utf-8")
    if "## Discovery ladder" not in ref_text:
        issues.append(
            f"{PREFIX_ROUTING} agent-triage/reference.md missing "
            f"§ Discovery ladder — Signature: {DISCOVERY_LADDER_SIGNATURE}"
        )
    if DISCOVERY_LADDER_SIGNATURE not in ref_text:
        issues.append(
            f"{PREFIX_ROUTING} agent-triage/reference.md missing "
            f"Signature `{DISCOVERY_LADDER_SIGNATURE}`"
        )
    if "```mermaid" not in ref_text or "flowchart" not in ref_text:
        issues.append(
            f"{PREFIX_ROUTING} agent-triage/reference.md § Discovery ladder "
            f"missing mermaid flowchart — Signature: {DISCOVERY_LADDER_SIGNATURE}"
        )
    for token in DISCOVERY_LADDER_BRANCH_TOKENS:
        if token not in ref_text.split("## Discovery ladder", 1)[-1].split("## ", 1)[0]:
            issues.append(
                f"{PREFIX_ROUTING} agent-triage/reference.md § Discovery ladder "
                f"missing branch `{token}` — Signature: {DISCOVERY_LADDER_SIGNATURE}"
            )
    for rel, tokens in DISCOVERY_LADDER_REQUIRED_TOKENS.items():
        path = repo_root / rel
        if not path.is_file():
            issues.append(f"{PREFIX_ROUTING} missing discovery-ladder artifact `{rel}`")
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                issues.append(
                    f"{PREFIX_ROUTING} `{rel}` missing discovery-ladder token "
                    f"`{token}` — Signature: {DISCOVERY_LADDER_SIGNATURE}"
                )
    return issues


def collect_governance_rule_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for pattern in GOVERNANCE_RULE_GLOBS:
        paths.extend(sorted(repo_root.glob(pattern)))
    return paths


def _resolve_baseline_glob(repo_root: Path, pattern: str) -> list[Path]:
    if "*" in pattern:
        return sorted(repo_root.glob(pattern))
    path = repo_root / pattern
    return [path] if path.is_file() else []


def collect_baseline_artifact_paths(repo_root: Path) -> list[tuple[str, Path]]:
    """Return (relative path, absolute path) for gc0 baseline artifacts."""
    seen: set[str] = set()
    results: list[tuple[str, Path]] = []
    for pattern in GOVERNANCE_COMPACT_BASELINE_GLOBS:
        for path in _resolve_baseline_glob(repo_root, pattern):
            rel = path.relative_to(repo_root).as_posix()
            if rel in seen:
                continue
            seen.add(rel)
            results.append((rel, path))
    return results


def line_count_for_path(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def section_line_count(text: str, heading: str) -> int:
    body = _section_after(text, heading)
    if not body:
        return 0
    return len([line for line in body.splitlines() if line.strip()])


def collect_duplication_pair_counts(repo_root: Path) -> list[tuple[str, str, int]]:
    rows: list[tuple[str, str, int]] = []
    for label, rel_path, heading in DUPLICATION_PAIR_SECTIONS:
        path = repo_root / rel_path
        if not path.is_file():
            rows.append((label, rel_path, 0))
            continue
        count = section_line_count(path.read_text(encoding="utf-8"), heading)
        rows.append((label, rel_path, count))
    kanban_skill = repo_root / ".cursor/skills/kanban-markdown/SKILL.md"
    kanban_rules = sorted(repo_root.glob(".cursor/rules/kanban-*.mdc"))
    if kanban_skill.is_file():
        skill_lines = line_count_for_path(kanban_skill)
        rule_lines = sum(line_count_for_path(path) for path in kanban_rules)
        skill_rel = kanban_skill.relative_to(repo_root).as_posix()
        rows.append(("kanban-markdown SKILL (lifecycle)", skill_rel, skill_lines))
        kanban_ref = repo_root / ".cursor/skills/kanban-markdown/reference.md"
        if kanban_ref.is_file():
            ref_lines = line_count_for_path(kanban_ref)
            rows.append(
                (
                    "kanban-markdown reference",
                    kanban_ref.relative_to(repo_root).as_posix(),
                    ref_lines,
                )
            )
        rows.append(
            (
                "kanban-*.mdc (sum)",
                ".cursor/rules/kanban-*.mdc",
                rule_lines,
            )
        )
    return rows


def _is_governance_always_on_rule(rel_path: str) -> bool:
    name = Path(rel_path).name
    if name.startswith("agent-") or name.startswith("kanban-"):
        return True
    return name in {"testing.mdc", "agent-routing.mdc"}


def collect_always_apply_rules(repo_root: Path) -> list[tuple[str, int, bool]]:
    rules_dir = repo_root / ".cursor/rules"
    if not rules_dir.is_dir():
        return []
    rows: list[tuple[str, int, bool]] = []
    for path in sorted(rules_dir.glob("*.mdc")):
        text = path.read_text(encoding="utf-8")
        if not _ALWAYS_APPLY_RE.search(text):
            continue
        rel = path.relative_to(repo_root).as_posix()
        rows.append((rel, line_count_for_path(path), _is_governance_always_on_rule(rel)))
    return rows


def format_line_count_report(repo_root: Path) -> str:
    """Human-readable gc0 baseline: artifact sizes, duplication pairs, always-on rules."""
    artifacts = collect_baseline_artifact_paths(repo_root)
    sized = [(rel, line_count_for_path(path)) for rel, path in artifacts if path.is_file()]
    sized.sort(key=lambda item: (-item[1], item[0]))
    total = sum(count for _rel, count in sized)

    lines = [
        "Governance compaction baseline (gc0)",
        f"Artifacts: {len(sized)} files, {total} lines total",
        "",
        "Top artifacts by line count:",
    ]
    for rel, count in sized:
        lines.append(f"  {count:5d}  {rel}")

    dup_rows = collect_duplication_pair_counts(repo_root)
    lines.extend(["", "Duplication pairs (section line counts):"])
    for label, rel_path, count in dup_rows:
        lines.append(f"  {count:5d}  {label} — {rel_path}")

    always_on = collect_always_apply_rules(repo_root)
    gov_lines = sum(count for _rel, count, is_gov in always_on if is_gov)
    all_lines = sum(count for _rel, count, _is_gov in always_on)
    lines.extend(
        [
            "",
            f"Always-on rules ({len(always_on)} files, {all_lines} lines; "
            f"{gov_lines} governance-related):",
        ]
    )
    for rel, count, is_gov in always_on:
        tag = "governance" if is_gov else "other"
        lines.append(f"  {count:5d}  {rel} ({tag})")

    return "\n".join(lines)


def check_lessons_coverage_drift(
    features_dir: Path,
    *,
    threshold: float = 75.0,
    include_severity: bool = True,
) -> list[str]:
    """Emit drift alert when composite lessons coverage is below threshold."""
    from scripts.lessons_coverage_lib import (
        build_report,
        format_lessons_coverage_drift_message,
        kanban_done_data_available,
        lessons_coverage_drift_severity,
    )
    from scripts.resolve_prior_lessons import find_done_lessons

    if not kanban_done_data_available(features_dir):
        return []

    report = build_report(features_dir, find_lessons=find_done_lessons)
    if report.composite is None:
        return []
    composite_pct = report.composite * 100
    if composite_pct >= threshold:
        return []

    message = format_lessons_coverage_drift_message(report, threshold=threshold)
    severity = lessons_coverage_drift_severity(report.composite)
    if include_severity:
        return [format_drift_line(message, severity=severity)]
    return [message]


def report_governance_line_counts(repo_root: Path) -> str:
    """Print and return the gc0 baseline report (Signature: governance-compact-baseline)."""
    report = format_line_count_report(repo_root)
    print(report)
    return report


def run_compaction_audit(
    *,
    repo_root: Path,
    features_dir: Path,
    quiet: bool = False,
    spawn_cards: bool = False,
    include_severity: bool = True,
) -> int:
    """Advisory compaction drift vs compaction-baseline.yaml (exit 0)."""
    from scripts.governance_compaction_lib import compaction_drift_lines

    lines = compaction_drift_lines(
        repo_root,
        include_severity=include_severity,
        min_severity=SEVERITY_WARN,
    )
    if spawn_cards and lines:
        created = create_drift_alert_cards(lines, features_dir=features_dir)
        if created and not quiet:
            for path in created:
                try:
                    display = path.relative_to(repo_root)
                except ValueError:
                    display = path
                print(f"drift card created: {display}", file=sys.stderr)
    if lines and not quiet:
        print("\n".join(lines))
    return 0


def run_duplication_threshold_audit(
    *,
    repo_root: Path,
    features_dir: Path,
    quiet: bool = False,
    spawn_cards: bool = False,
    include_severity: bool = True,
) -> int:
    """Fail parity when duplication pairs exceed post-compaction caps (exit 1)."""
    from scripts.governance_compaction_lib import duplication_threshold_lines

    lines = duplication_threshold_lines(
        repo_root,
        include_severity=include_severity,
        min_severity=SEVERITY_WARN,
    )
    if spawn_cards and lines:
        created = create_drift_alert_cards(lines, features_dir=features_dir)
        if created and not quiet:
            for path in created:
                try:
                    display = path.relative_to(repo_root)
                except ValueError:
                    display = path
                print(f"drift card created: {display}", file=sys.stderr)
    if lines and not quiet:
        print("\n".join(lines))
    return 1 if lines else 0


def format_forward_feedback_audit_report(
    hits: list[tuple[str, list[str]]],
) -> list[str]:
    """Format gc7 advisory lines for present parent forward-feedback field gaps (fcp3)."""
    from scripts.lessons_coverage_lib import C1B_FORWARD_FEEDBACK_GRANDFATHER_DATE

    signature = "governance-gc7-forward-feedback-audit"
    if not hits:
        return [
            f"{PREFIX_FORWARD_FEEDBACK} present parent ff blocks pass field audit "
            f"(post-{C1B_FORWARD_FEEDBACK_GRANDFATHER_DATE}; parent ff optional when absent) — "
            f"Signature: {signature}",
        ]
    lines = [
        f"{PREFIX_FORWARD_FEEDBACK} {len(hits)} card(s) with gc5 gaps (Signature: {signature}):",
    ]
    for rel, card_issues in hits:
        for issue in card_issues:
            lines.append(f"  {rel}: {issue}")
    return lines


def run_forward_feedback_audit(
    *,
    features_dir: Path,
    quiet: bool = False,
) -> int:
    """Advisory gc7 scan — always exit 0; does not spawn drift cards."""
    from scripts.lessons_coverage_lib import (
        audit_forward_feedback_gc5,
        audit_phase_epic_ff_policy_advisory,
    )

    hits = audit_forward_feedback_gc5(features_dir=features_dir)
    lines = format_forward_feedback_audit_report(hits)
    advisory = audit_phase_epic_ff_policy_advisory(features_dir=features_dir)
    if advisory:
        lines.append("Forward feedback phase-policy advisory (card-done-forward-feedback-cadence):")
        lines.extend(advisory)
    if not quiet:
        print("\n".join(lines))
    return 0


def _is_allowed_development_md_section_line(line: str) -> bool:
    """Meta lines that mention the grep pattern but are not stale governance § links."""
    lowered = line.lower()
    if 'rg "' in line and "development.md §" in line:
        return True
    if "development.md §" in line and ("zero" in lowered or "no stale" in lowered):
        return True
    if "not `development.md §" in line or "not development.md §" in line:
        return True
    if "`docs/development.md §` zero" in line:
        return True
    return "§ anchors remain" in line


def _iter_docs_governance_split_scan_files(repo_root: Path) -> list[Path]:
    roots: list[Path] = [
        repo_root / ".cursor",
        repo_root / "docs",
        repo_root / "scripts",
        repo_root / "AGENTS.md",
    ]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            if root.suffix in _DOCS_GOVERNANCE_SCAN_SUFFIXES:
                files.append(root)
            continue
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in _DOCS_GOVERNANCE_SCAN_SUFFIXES:
                continue
            try:
                rel = path.relative_to(repo_root).as_posix()
            except ValueError:
                continue
            if rel in _DOCS_GOVERNANCE_EXCLUDE_REL:
                continue
            files.append(path)
    return sorted(files)


def find_stale_development_md_section_refs(repo_root: Path) -> list[tuple[str, int, str]]:
    """Return (rel_path, line_no, line_text) for stale development.md § anchors."""
    hits: list[tuple[str, int, str]] = []
    for path in _iter_docs_governance_split_scan_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not _STALE_DEV_MD_SECTION_RE.search(line):
                continue
            if _is_allowed_development_md_section_line(line):
                continue
            hits.append((rel, line_no, line.strip()))
    return hits


def format_docs_governance_split_report(
    hits: list[tuple[str, int, str]],
    *,
    repo_root: Path,
) -> list[str]:
    """Advisory lines for DocsGovernanceSplit residual § scan (Signature: docs-governance-split)."""
    dev_md = repo_root / "docs" / "development.md"
    gov_dir = repo_root / "docs" / "governance"
    dev_lines = line_count_for_path(dev_md) if dev_md.is_file() else 0
    gov_lines = sum(
        line_count_for_path(path) for path in sorted(gov_dir.glob("*.md")) if path.is_file()
    )
    summary = (
        f"development.md {dev_lines} lines; docs/governance/ {gov_lines} lines "
        f"(Signature: {_DOCS_GOVERNANCE_SPLIT_SIGNATURE})"
    )
    if not hits:
        return [
            f"{PREFIX_DOCS_GOVERNANCE_SPLIT} no stale development.md § anchors — {summary}",
        ]
    lines = [
        f"{PREFIX_DOCS_GOVERNANCE_SPLIT} {len(hits)} stale development.md § anchor(s) — {summary}:",
    ]
    for rel, line_no, text in hits:
        preview = text if len(text) <= 96 else text[:93] + "..."
        lines.append(f"  {rel}:{line_no}: {preview}")
    return lines


def run_docs_governance_split_audit(
    *,
    repo_root: Path,
    quiet: bool = False,
) -> int:
    """Advisory dg3 scan — always exit 0; does not spawn drift cards."""
    hits = find_stale_development_md_section_refs(repo_root)
    lines = format_docs_governance_split_report(hits, repo_root=repo_root)
    if not quiet:
        print("\n".join(lines))
    return 0


def run_forward_feedback_stale_audit(
    *,
    index_path: Path,
    stale_days: int,
    quiet: bool = False,
) -> int:
    """Advisory ff3 stale metrics — always exit 0; backlog SSOT not card fields."""
    from scripts.forward_feedback_index_lib import (
        find_stale_high_risk_open,
        format_stale_advisory_lines,
        load_index,
    )

    if stale_days < 0:
        raise ValueError("--stale-days must be >= 0")
    payload = load_index(index_path)
    records = payload.get("items") or []
    if not isinstance(records, list):
        records = []
    stale_items = find_stale_high_risk_open(records, stale_days=stale_days)
    body_lines = format_stale_advisory_lines(stale_items, stale_days=stale_days)
    lines = [f"{PREFIX_FORWARD_FEEDBACK_STALE} {body_lines[0]}"]
    lines.extend(body_lines[1:])
    if not quiet:
        print("\n".join(lines))
    return 0


def run_checks(
    *,
    repo_root: Path,
    agents_text: str,
    triage_text: str,
    feature_areas_text: str,
    features_dir: Path,
    rule_paths: list[Path] | None = None,
    reference_paths: tuple[Path, Path] | None = None,
    triage_reference_text: str | None = None,
    lessons_index_text: str | None = None,
    include_severity: bool = True,
) -> list[str]:
    rule_paths = rule_paths or collect_governance_rule_paths(repo_root)
    reference_paths = reference_paths or (SELF_EVAL_REFERENCE, PRE_COMMIT_REFERENCE)
    triage_reference_path = repo_root / ".cursor/skills/agent-triage/reference.md"
    lessons_index_path = repo_root / "docs/lessons-index.yaml"
    if triage_reference_text is None:
        triage_reference_text = triage_reference_path.read_text(encoding="utf-8")
    if lessons_index_text is None:
        lessons_index_text = lessons_index_path.read_text(encoding="utf-8")

    issues: list[str] = []
    issues.extend(check_classify_parity(agents_text, triage_text, triage_reference_text))

    self_eval_skill_path = repo_root / ".cursor/skills/agent-self-evaluation/SKILL.md"
    if self_eval_skill_path.is_file():
        skill_text = self_eval_skill_path.read_text(encoding="utf-8")
        issues.extend(check_handoff_duplication_pair(agents_text, skill_text))

    reference_sigs = extract_reference_signatures(
        *reference_paths,
        triage_reference_path,
    )
    rule_cites = extract_rule_signature_cites(rule_paths)
    issues.extend(check_failure_pattern_parity(reference_sigs, rule_cites))

    schema_entries = load_area_schema_entries(feature_areas_text)
    issues.extend(
        check_area_schema_parity(
            repo_root,
            schema_entries,
            triage_reference_text,
            lessons_index_text,
            reference_sigs,
        )
    )

    from scripts.sync_agents_area_table import check_agents_area_table_parity

    issues.extend(check_agents_area_table_parity(agents_text, schema_entries, feature_areas_text))

    yaml_paths = load_agent_workflow_paths(feature_areas_text)
    workflow_entries = [entry for entry in schema_entries if entry.name == "Agent Workflow"]
    agents_paths = extract_agents_governance_paths(agents_text, workflow_entries)
    issues.extend(check_registry_parity(yaml_paths, agents_paths))

    handlers_by_area = load_area_handlers(feature_areas_text)
    issues.extend(check_handlers_registry_parity(handlers_by_area))
    issues.extend(check_kanban_label_methods_handlers(features_dir, handlers_by_area))

    card_labels = collect_feature_card_labels(features_dir)
    agents_card_labels = parse_agents_card_type_labels(agents_text)
    issues.extend(check_card_type_parity(card_labels, agents_card_labels))
    issues.extend(check_kanban_rule_globs(repo_root))
    issues.extend(check_index_not_grep_routing(repo_root))
    issues.extend(check_discovery_ladder_routing(repo_root))

    parity_issues = apply_severity(issues, include_severity=include_severity)
    lessons_issues = check_lessons_coverage_drift(
        features_dir,
        include_severity=include_severity,
    )
    return parity_issues + lessons_issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout; exit code only",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Omit [severity] prefix (phase 1–3 line format)",
    )
    parser.add_argument(
        "--no-spawn-cards",
        action="store_true",
        help="Do not create kanban cards under .devtool/features/",
    )
    parser.add_argument(
        "--features-dir",
        type=Path,
        default=None,
        help="Kanban features directory (default: .devtool/features)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--line-counts",
        action="store_true",
        help="Print gc0 governance artifact line-count baseline and exit 0",
    )
    parser.add_argument(
        "--compaction",
        action="store_true",
        help=(
            "Advisory compaction drift vs compaction-baseline.yaml (exit 0; "
            "Signature: governance-compaction-drift-alert)"
        ),
    )
    parser.add_argument(
        "--duplication-threshold",
        action="store_true",
        help=(
            "Fail when Classify trio or kanban lifecycle pairs exceed "
            "compaction-baseline.yaml caps (Signature: governance-duplication-automation)"
        ),
    )
    parser.add_argument(
        "--forward-feedback-audit",
        action="store_true",
        help=(
            "Advisory gc5 field scan on post-grandfather done/archived cards (exit 0; "
            "Signature: governance-gc7-forward-feedback-audit)"
        ),
    )
    parser.add_argument(
        "--forward-feedback-stale",
        action="store_true",
        help=(
            "Advisory ff3 stale backlog metrics from forward-feedback-index.yaml "
            "(exit 0; Signature: forward-feedback-stale-metrics)"
        ),
    )
    parser.add_argument(
        "--docs-governance-split",
        action="store_true",
        help=(
            "Advisory DocsGovernanceSplit residual development.md § scan (exit 0; "
            "Signature: docs-governance-split)"
        ),
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=None,
        metavar="N",
        help="Days since completed_at for --forward-feedback-stale (default: 30)",
    )
    args = parser.parse_args(argv)
    root = args.repo_root
    features_dir = args.features_dir or (root / ".devtool" / "features")

    if args.line_counts:
        if not args.quiet:
            report_governance_line_counts(root)
        return 0

    if args.compaction:
        return run_compaction_audit(
            repo_root=root,
            features_dir=features_dir,
            quiet=args.quiet,
            spawn_cards=not args.no_spawn_cards,
            include_severity=not args.plain,
        )

    if args.duplication_threshold:
        return run_duplication_threshold_audit(
            repo_root=root,
            features_dir=features_dir,
            quiet=args.quiet,
            spawn_cards=not args.no_spawn_cards,
            include_severity=not args.plain,
        )

    if args.forward_feedback_audit:
        return run_forward_feedback_audit(features_dir=features_dir, quiet=args.quiet)

    if args.forward_feedback_stale:
        from scripts.forward_feedback_index_lib import DEFAULT_STALE_DAYS

        stale_days = args.stale_days if args.stale_days is not None else DEFAULT_STALE_DAYS
        try:
            return run_forward_feedback_stale_audit(
                index_path=root / "docs" / "forward-feedback-index.yaml",
                stale_days=stale_days,
                quiet=args.quiet,
            )
        except ValueError as exc:
            print(f"check_governance_parity: {exc}", file=sys.stderr)
            return 2

    if args.docs_governance_split:
        return run_docs_governance_split_audit(repo_root=root, quiet=args.quiet)

    if yaml is None:
        print("check_governance_parity: PyYAML not installed", file=sys.stderr)
        return 2

    try:
        issues = run_checks(
            repo_root=root,
            agents_text=(root / "AGENTS.md").read_text(encoding="utf-8"),
            triage_text=(root / ".cursor/skills/agent-triage/SKILL.md").read_text(encoding="utf-8"),
            feature_areas_text=(root / "docs/feature-areas.yaml").read_text(encoding="utf-8"),
            features_dir=features_dir,
            include_severity=not args.plain,
        )
    except FileNotFoundError as exc:
        print(f"check_governance_parity: {exc}", file=sys.stderr)
        return 2

    if issues and not args.no_spawn_cards:
        created = create_drift_alert_cards(issues, features_dir=features_dir)
        if created and not args.quiet:
            for path in created:
                try:
                    display = path.relative_to(root)
                except ValueError:
                    display = path
                print(f"drift card created: {display}", file=sys.stderr)

    if issues and not args.quiet:
        print("\n".join(issues))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
