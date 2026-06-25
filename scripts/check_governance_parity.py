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

AGENTS_MD = REPO_ROOT / "AGENTS.md"
TRIAGE_SKILL = REPO_ROOT / ".cursor/skills/agent-triage/SKILL.md"
FEATURE_AREAS = REPO_ROOT / "docs/feature-areas.yaml"
FEATURES_DIR = REPO_ROOT / ".devtool/features"

SELF_EVAL_REFERENCE = REPO_ROOT / ".cursor/skills/agent-self-evaluation/reference.md"
PRE_COMMIT_REFERENCE = REPO_ROOT / ".cursor/skills/pre-commit-workflow/reference.md"

GOVERNANCE_RULE_GLOBS = (
    ".cursor/rules/agent-*.mdc",
    ".cursor/rules/kanban-*.mdc",
    ".cursor/rules/testing.mdc",
)

PREFIX_ROUTING = "Routing drift alert:"
PREFIX_CARD = "Card-type drift alert:"
PREFIX_FAILURE = "Failure-pattern drift alert:"
PREFIX_REGISTRY = "Registry drift alert:"

SEVERITY_INFO = "info"
SEVERITY_WARN = "warn"
SEVERITY_CRITICAL = "critical"

DEFAULT_SEVERITY_BY_PREFIX: dict[str, str] = {
    PREFIX_ROUTING: SEVERITY_WARN,
    PREFIX_CARD: SEVERITY_WARN,
    PREFIX_FAILURE: SEVERITY_CRITICAL,
    PREFIX_REGISTRY: SEVERITY_WARN,
}

EPIC_GOVERNANCE_DRIFT = "GovernanceDriftAlert"

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
        ".cursor/rules/kanban-bug-cards.mdc",
        ".cursor/rules/kanban-commit-issue-cards.mdc",
        ".cursor/rules/kanban-inquiry-cards.mdc",
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
_LABELS_RE = re.compile(r"^labels:\s*\[(.*?)\]", re.MULTILINE)
_AGENTS_RULE_LINK_RE = re.compile(r"\[([^\]]+)\]\((\.cursor/rules/[a-z0-9_-]+\.mdc)\)")
_AGENTS_SKILL_LINK_RE = re.compile(
    r"\[([^\]]+)\]\((\.cursor/skills/(?:agent|kanban|pre-commit-workflow)[^)]*)\)"
)

_HANDLER_SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*(?:\*)?$")

# Anchor phrases for Classify quickly ↔ triage §1 parity (order matters for messages).
CLASSIFY_ANCHORS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("kanban card", ("kanban card",)),
    ("governance audit", ("governance audit",)),
    ("explain / audit", ("explain", "is this correct")),
    ("ad-hoc bug", ("one error", "ad-hoc bug", "lint, typo")),
    ("multi-file feature", ("multi-file", "no card", "refactor (no card)")),
    ("pre-commit failed", ("pre-commit failed",)),
    ("pytest / ruff", ("failing test", "pytest", "ruff / lint")),
    ("ui wiring", ("ui wiring", "dialog not persisting")),
    ("agent handoff", ("agent handoff", "process mistake")),
    ("repeated churn", ("repeated mistake", "familiar churn", "churn")),
    ("run tests / commit-ready", ("run tests", "commit-ready", '"run tests"')),
    ("area lesson lookup", ("area lesson lookup", "lessons by area")),
)


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
            "Restore Classify quickly ↔ agent-triage §1 parity per "
            "[agent-triage/reference.md](../../.cursor/skills/agent-triage/reference.md) "
            "§ Consistency matrix and § Drift alert examples."
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
            "Sync `docs/feature-areas.yaml` **Agent Workflow** `paths` with "
            "AGENTS.md area → skills & rules table (Agent + Kanban rows); fix "
            "`handlers:` duplicates, malformed symbols, or kanban **Label Methods** "
            "symbols missing from the registry."
        ),
    }
    return actions.get(prefix, actions[PREFIX_ROUTING])


def card_title_for_issue(issue: DriftIssue) -> str:
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
    return None


def build_drift_card_body(issue: DriftIssue) -> str:
    label_paths = label_paths_for_issue(issue)
    feature_areas = feature_areas_for_issue(issue)
    title = card_title_for_issue(issue)
    paths_md = "\n".join(f"- `{path}`" for path in label_paths)
    areas_md = "\n".join(f"`{area}`" for area in feature_areas)
    return f"""# {title}

Spawned by `scripts/check_governance_parity.py` (epic **{EPIC_GOVERNANCE_DRIFT}**).

## Alert

{issue.message}

## Feature Areas

{areas_md}

## Label Paths

{paths_md}

## Corrective Action

{corrective_action_for_issue(issue)}
"""


def create_drift_alert_cards(
    issues: list[str],
    *,
    features_dir: Path,
) -> list[Path]:
    """Create one todo kanban card per drift issue; skip duplicates by ## Alert text."""
    features_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    for line in issues:
        issue = parse_drift_line(line)
        existing = _find_existing_card_for_alert(features_dir, issue.message)
        if existing is not None:
            continue

        card_id = issue_card_id(issue)
        path = features_dir / f"{card_id}.md"
        if path.exists():
            continue

        priority = priority_for_severity(issue.severity)
        order = _next_order(features_dir)
        frontmatter = f"""---
id: "{card_id}"
status: "todo"
priority: "{priority}"
assignee: null
epic: "{EPIC_GOVERNANCE_DRIFT}"
dueDate: null
created: "{now}"
modified: "{now}"
completedAt: null
labels: []
order: "{order}"
---
"""
        path.write_text(frontmatter + build_drift_card_body(issue), encoding="utf-8")
        created.append(path)

    return created


def check_classify_parity(
    agents_text: str,
    triage_text: str,
) -> list[str]:
    agents_section = _section_after(agents_text, "## Classify quickly")
    triage_section = _section_after(triage_text, "## 1. Classify the request")
    issues: list[str] = []
    for name, phrases in CLASSIFY_ANCHORS:
        in_agents = _contains_anchor(agents_section, phrases)
        in_triage = _contains_anchor(triage_section, phrases)
        if in_agents and not in_triage:
            issues.append(f'{PREFIX_ROUTING} AGENTS Classify row "{name}" missing in triage §1')
        elif in_triage and not in_agents:
            issues.append(
                f'{PREFIX_ROUTING} triage §1 row "{name}" missing in AGENTS Classify quickly'
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
    section = _section_after(card_text, "## Label Methods")
    if not section.strip():
        return set()
    return _handler_symbols_from_label_methods_section(section)


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
    """Label Methods symbols on open cards must exist in feature-areas.yaml handlers."""
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
                    f"{PREFIX_REGISTRY} kanban `{path.name}` Label Methods `{symbol}` "
                    "missing from feature-areas.yaml `handlers:`"
                )

    return issues


def _skill_link_to_path(link: str) -> str:
    if link.endswith("/SKILL.md"):
        return link[: -len("SKILL.md")]
    return _normalize_path(link)


def extract_agents_governance_paths(agents_text: str) -> set[str]:
    section = _section_after(agents_text, "## Area → skills & rules")
    paths: set[str] = {"AGENTS.md"}
    for line in section.splitlines():
        if "Agent / routing" not in line and "Kanban /" not in line:
            continue
        for _name, rule_path in _AGENTS_RULE_LINK_RE.findall(line):
            paths.add(_normalize_path(rule_path))
        for _name, skill_path in _AGENTS_SKILL_LINK_RE.findall(line):
            paths.add(_skill_link_to_path(skill_path))
    return paths


def check_registry_parity(
    yaml_paths: set[str],
    agents_paths: set[str],
) -> list[str]:
    issues: list[str] = []
    for path in sorted(yaml_paths - agents_paths):
        issues.append(
            f"{PREFIX_REGISTRY} feature-areas.yaml lists `{path}` not reflected in "
            "AGENTS Agent/Kanban area rows"
        )
    for path in sorted(agents_paths - yaml_paths):
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


def collect_governance_rule_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for pattern in GOVERNANCE_RULE_GLOBS:
        paths.extend(sorted(repo_root.glob(pattern)))
    return paths


def run_checks(
    *,
    repo_root: Path,
    agents_text: str,
    triage_text: str,
    feature_areas_text: str,
    features_dir: Path,
    rule_paths: list[Path] | None = None,
    reference_paths: tuple[Path, Path] | None = None,
    include_severity: bool = True,
) -> list[str]:
    rule_paths = rule_paths or collect_governance_rule_paths(repo_root)
    reference_paths = reference_paths or (SELF_EVAL_REFERENCE, PRE_COMMIT_REFERENCE)

    issues: list[str] = []
    issues.extend(check_classify_parity(agents_text, triage_text))

    reference_sigs = extract_reference_signatures(*reference_paths)
    rule_cites = extract_rule_signature_cites(rule_paths)
    issues.extend(check_failure_pattern_parity(reference_sigs, rule_cites))

    yaml_paths = load_agent_workflow_paths(feature_areas_text)
    agents_paths = extract_agents_governance_paths(agents_text)
    issues.extend(check_registry_parity(yaml_paths, agents_paths))

    handlers_by_area = load_area_handlers(feature_areas_text)
    issues.extend(check_handlers_registry_parity(handlers_by_area))
    issues.extend(check_kanban_label_methods_handlers(features_dir, handlers_by_area))

    card_labels = collect_feature_card_labels(features_dir)
    agents_card_labels = parse_agents_card_type_labels(agents_text)
    issues.extend(check_card_type_parity(card_labels, agents_card_labels))

    return apply_severity(issues, include_severity=include_severity)


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
    args = parser.parse_args(argv)
    root = args.repo_root
    features_dir = args.features_dir or (root / ".devtool" / "features")

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
