"""Shared helpers for lessons coverage audits (C1–C4)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from scripts.check_governance_parity import extract_reference_signatures
from scripts.resolve_prior_lessons import (
    _ARTIFACTS_BULLET_RE,
    REPO_ROOT,
    _closed_card_dirs,
    _lessons_excerpt,
    _parse_frontmatter,
    _path_overlaps,
    extract_feature_area_labels,
    extract_governance_artifacts,
    extract_label_paths,
    extract_prior_lessons_citations,
    extract_signatures,
    find_done_lessons,
    parse_artifacts_line,
)

_SIGNATURE_TABLE_PATHS = (
    REPO_ROOT / ".cursor/skills/pre-commit-workflow/reference.md",
    REPO_ROOT / ".cursor/skills/agent-self-evaluation/reference.md",
)

_ACTIVE_STATUSES = frozenset({"todo", "in-progress", "review"})
_C1B_LABELS = frozenset({"feature", "bug", "agent", "commit-issue"})
# lc4c ship date — done cards completed before this without forward feedback grandfather as pass.
C1B_FORWARD_FEEDBACK_GRANDFATHER_DATE = "2026-06-27"
_FORWARD_FEEDBACK_HEADING_RE = re.compile(
    r"^## Forward-looking feedback[^\n]*\n",
    re.MULTILINE,
)
GC5_FORWARD_FEEDBACK_CATEGORIES = (
    "Governance",
    "Skill",
    "Rule",
    "Codebase",
    "Prompt pattern",
    "Routing",
)
_RISK_LEVEL_RE = re.compile(r"\*\*Risk Level:\*\*\s*(\d+)", re.IGNORECASE)
_IMPACT_SCOPE_RANK = {"system-wide": 3, "multi-card": 2, "local": 1}
_IMPORTANCE_RANK = {"primary": 3, "secondary": 2, "tertiary": 1}
GC5_CATEGORY_ALIASES: dict[str, str] = {
    "governance": "Governance",
    "routing": "Routing",
    "rule": "Rule",
    "rules": "Rule",
    "skill": "Skill",
    "skills": "Skill",
    "codebase": "Codebase",
    "prompt pattern": "Prompt pattern",
    "prompt": "Prompt pattern",
    "prompt-pattern": "Prompt pattern",
}
_CONTEXT_CARD_LINK_RE = re.compile(
    r"\]\((?:\.\./)?(?:done|archived)/([^)]+\.md)\)",
    re.IGNORECASE,
)


@dataclass
class MetricScore:
    """One sub-metric result (0.0–1.0 or None when N/A)."""

    name: str
    numerator: int
    denominator: int
    score: float | None
    detail: str = ""


@dataclass
class CoverageReport:
    """Full C1–C4 (+ C1b) audit output."""

    c1: MetricScore
    c1b: MetricScore
    c2: MetricScore
    c3: MetricScore
    c4: MetricScore
    c4_per_card: MetricScore
    composite: float | None
    per_card_c3: dict[str, MetricScore] = field(default_factory=dict)


def _known_signatures() -> set[str]:
    return extract_reference_signatures(*_SIGNATURE_TABLE_PATHS)


def _path_exists(path: str) -> bool:
    return (REPO_ROOT / path).is_file()


def _infer_path_type(path: str) -> str:
    if path.endswith("/reference.md") or path.endswith("reference.md"):
        return "reference"
    if path.startswith(".cursor/skills/"):
        return "skill"
    if path.startswith(".cursor/rules/") and path.endswith(".mdc"):
        return "rule"
    if path.startswith("docs/") or path == "AGENTS.md":
        return "doc"
    if path.startswith("tests/"):
        return "test"
    return "unknown"


def _path_type_is_correct(path: str) -> bool:
    return _infer_path_type(path) != "unknown"


def _iter_closed_cards() -> list[Path]:
    paths: list[Path] = []
    for directory in _closed_card_dirs():
        paths.extend(directory.glob("*.md"))
    return sorted(paths)


def _iter_active_cards(features_dir: Path) -> list[Path]:
    if not features_dir.is_dir():
        return []
    paths = [
        path
        for path in features_dir.glob("*.md")
        if str(_parse_frontmatter(path.read_text(encoding="utf-8")).get("status") or "")
        in _ACTIVE_STATUSES
    ]
    return sorted(paths)


def _cards_with_lessons() -> list[tuple[Path, str]]:
    hits: list[tuple[Path, str]] = []
    for card_path in _iter_closed_cards():
        text = card_path.read_text(encoding="utf-8")
        excerpt = _lessons_excerpt(text)
        if excerpt is not None:
            hits.append((card_path, excerpt))
    return hits


def _resolved_card_has_promotion(lessons_text: str, known_sigs: set[str]) -> bool:
    if any(_path_exists(path) for path in extract_governance_artifacts(lessons_text)):
        return True
    return any(sig in known_sigs for sig in extract_signatures(lessons_text))


def _collect_c2_refs(lessons_text: str) -> list[tuple[str, str]]:
    """Return (ref, source) pairs — source is ``artifacts`` or ``heuristic``."""
    refs: list[tuple[str, str]] = []
    seen: set[str] = set()

    for line in lessons_text.splitlines():
        if not _ARTIFACTS_BULLET_RE.match(line):
            continue
        parsed = parse_artifacts_line(line)
        for path in parsed.repo_paths():
            if path not in seen:
                seen.add(path)
                refs.append((path, "artifacts"))
        for sig in parsed.signatures:
            key = f"sig:{sig}"
            if key not in seen:
                seen.add(key)
                refs.append((sig, "artifacts"))

    if refs:
        return refs

    for path in extract_governance_artifacts(lessons_text):
        if path not in seen:
            seen.add(path)
            refs.append((path, "heuristic"))
    for sig in extract_signatures(lessons_text):
        key = f"sig:{sig}"
        if key not in seen:
            seen.add(key)
            refs.append((sig, "heuristic"))
    return refs


def _ref_is_correctly_typed(ref: str, source: str, known_sigs: set[str]) -> bool:
    if ref in known_sigs:
        return ref in known_sigs
    if _infer_path_type(ref) == "test":
        return True
    if source == "artifacts":
        return _path_type_is_correct(ref)
    return _path_type_is_correct(ref)


def _card_label_set(meta: dict) -> set[str]:
    raw = meta.get("labels") or []
    if not isinstance(raw, list):
        return set()
    return {str(item).strip() for item in raw if str(item).strip()}


def _has_forward_feedback(text: str) -> bool:
    return _FORWARD_FEEDBACK_HEADING_RE.search(text) is not None


def _completed_before_grandfather(meta: dict) -> bool:
    raw = meta.get("completedAt")
    if not raw:
        return False
    completed = str(raw)[:10]
    return completed < C1B_FORWARD_FEEDBACK_GRANDFATHER_DATE


def audit_forward_feedback_coverage() -> MetricScore:
    """C1b — done cards with forward feedback / label-scoped cards with lessons captured."""
    lesson_cards: list[tuple[Path, str, dict]] = []
    for card_path in _iter_closed_cards():
        text = card_path.read_text(encoding="utf-8")
        excerpt = _lessons_excerpt(text)
        if excerpt is None:
            continue
        meta = _parse_frontmatter(text)
        if not (_card_label_set(meta) & _C1B_LABELS):
            continue
        lesson_cards.append((card_path, text, meta))

    if not lesson_cards:
        return MetricScore(
            "C1b Forward feedback",
            0,
            0,
            None,
            "no label-scoped done cards with lessons",
        )

    passed = 0
    for _, text, meta in lesson_cards:
        if _has_forward_feedback(text) or _completed_before_grandfather(meta):
            passed += 1

    score = passed / len(lesson_cards)
    return MetricScore(
        "C1b Forward feedback",
        passed,
        len(lesson_cards),
        score,
        (
            f"{passed}/{len(lesson_cards)} cards with forward feedback "
            f"(grandfather before {C1B_FORWARD_FEEDBACK_GRANDFATHER_DATE})"
        ),
    )


@dataclass
class ForwardFeedbackItem:
    category: str
    question: str
    risk_level: int | None = None
    impact_scope: str | None = None
    importance: str | None = None
    references: str | None = None
    mitigation: str | None = None
    detail: str | None = None
    priority: str | None = None
    seq: int = 0


def normalize_forward_feedback_category(raw: str) -> str | None:
    """Map CLI aliases to canonical gc5 category names."""
    key = raw.strip().lower()
    if key in GC5_CATEGORY_ALIASES:
        return GC5_CATEGORY_ALIASES[key]
    for category in GC5_FORWARD_FEEDBACK_CATEGORIES:
        if category.lower() == key:
            return category
    return None


def forward_feedback_section(text: str) -> str | None:
    return _forward_feedback_section(text)


def split_forward_feedback_categories(section: str) -> dict[str, str]:
    return _split_forward_feedback_categories(section)


def _extract_field_value(block: str, field: str) -> str | None:
    pattern = re.compile(
        rf"\*\*{re.escape(field)}:\*\*\s*(.*?)(?=\n\s*\*\*|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(block)
    if not match:
        return None
    value = " ".join(match.group(1).split())
    return value or None


def _parse_risk_level(block: str) -> int | None:
    match = _RISK_LEVEL_RE.search(block)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def parse_forward_feedback_item_block(
    category: str, block: str, *, seq: int
) -> ForwardFeedbackItem | None:
    question = _extract_field_value(block, "Question")
    if not question:
        return None
    return ForwardFeedbackItem(
        category=category,
        question=question,
        risk_level=_parse_risk_level(block),
        impact_scope=_extract_field_value(block, "Impact Scope"),
        importance=_extract_field_value(block, "Importance"),
        references=_extract_field_value(block, "References"),
        mitigation=_extract_field_value(block, "Mitigation"),
        detail=_extract_field_value(block, "Detail"),
        priority=_extract_field_value(block, "Priority"),
        seq=seq,
    )


def _split_category_items(body: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    for line in body.splitlines():
        if line.startswith("- ") and current:
            items.append("\n".join(current).strip())
            current = [line]
        elif line.startswith("- ") or current:
            current.append(line)
    if current:
        items.append("\n".join(current).strip())
    return [item for item in items if item]


def parse_forward_feedback_items(text: str) -> list[ForwardFeedbackItem]:
    """Extract gc5 forward-feedback question items from a closed kanban card."""
    section = _forward_feedback_section(text)
    if section is None:
        return []
    parsed: list[ForwardFeedbackItem] = []
    for category, body in _split_forward_feedback_categories(section).items():
        for seq, block in enumerate(_split_category_items(body), start=1):
            item = parse_forward_feedback_item_block(category, block, seq=seq)
            if item is not None:
                parsed.append(item)
    return parsed


def forward_feedback_rank_key(
    item: ForwardFeedbackItem,
    *,
    completed_at: str | None = None,
) -> tuple[int, int, int, str]:
    """Sort key: risk desc, impact scope desc, importance desc, age asc."""
    risk = item.risk_level if item.risk_level is not None else 0
    scope = _IMPACT_SCOPE_RANK.get((item.impact_scope or "").lower(), 0)
    importance = _IMPORTANCE_RANK.get((item.importance or "").lower(), 0)
    return (-risk, -scope, -importance, completed_at or "")


def iter_labeled_lesson_cards(
    *,
    features_dir: Path | None = None,
) -> list[tuple[Path, str, dict]]:
    """Closed cards with lessons captured and C1b label scope."""
    root_features = features_dir or (REPO_ROOT / ".devtool" / "features")
    cards: list[tuple[Path, str, dict]] = []
    for card_path in _iter_closed_cards_under(root_features):
        text = card_path.read_text(encoding="utf-8")
        if _lessons_excerpt(text) is None:
            continue
        meta = _parse_frontmatter(text)
        if not (_card_label_set(meta) & _C1B_LABELS):
            continue
        cards.append((card_path, text, meta))
    return cards


def _forward_feedback_section(text: str) -> str | None:
    match = _FORWARD_FEEDBACK_HEADING_RE.search(text)
    if not match:
        return None
    rest = text[match.end() :]
    next_heading = re.search(r"^## ", rest, re.MULTILINE)
    if next_heading:
        rest = rest[: next_heading.start()]
    return rest


def _split_forward_feedback_categories(section: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    parts = re.split(r"^### ", section, flags=re.MULTILINE)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split("\n", 1)
        name = lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""
        if name in GC5_FORWARD_FEEDBACK_CATEGORIES:
            blocks[name] = body
    return blocks


def _audit_forward_feedback_category(category: str, block: str) -> list[str]:
    issues: list[str] = []
    if not re.search(r"\*\*Question:\*\*", block):
        issues.append(f"{category}: missing Question")
    if "**Impact Scope:**" not in block:
        issues.append(f"{category}: missing Impact Scope")
    if "**References:**" not in block:
        issues.append(f"{category}: missing References")
    risks = [int(match.group(1)) for match in _RISK_LEVEL_RE.finditer(block)]
    if risks and max(risks) >= 4 and "**Mitigation:**" not in block:
        issues.append(f"{category}: missing Mitigation (risk ≥ 4)")
    return issues


def _audit_card_forward_feedback_gc5(text: str) -> list[str]:
    section = _forward_feedback_section(text)
    if section is None:
        return ["missing ## Forward-looking feedback"]
    blocks = _split_forward_feedback_categories(section)
    issues: list[str] = []
    for category in GC5_FORWARD_FEEDBACK_CATEGORIES:
        block = blocks.get(category, "")
        if not block.strip():
            issues.append(f"{category}: missing category section")
            continue
        issues.extend(_audit_forward_feedback_category(category, block))
    return issues


def _iter_closed_cards_under(features_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for sub in ("done", "archived"):
        directory = features_dir / sub
        if directory.is_dir():
            paths.extend(directory.glob("*.md"))
    return sorted(paths)


def audit_forward_feedback_gc5(*, features_dir: Path | None = None) -> list[tuple[str, list[str]]]:
    """gc7 — post-grandfather closed cards with gc5 forward-feedback field gaps."""
    root_features = features_dir or (REPO_ROOT / ".devtool" / "features")
    hits: list[tuple[str, list[str]]] = []
    for card_path in _iter_closed_cards_under(root_features):
        text = card_path.read_text(encoding="utf-8")
        if _lessons_excerpt(text) is None:
            continue
        meta = _parse_frontmatter(text)
        if not (_card_label_set(meta) & _C1B_LABELS):
            continue
        if _completed_before_grandfather(meta):
            continue
        card_issues = _audit_card_forward_feedback_gc5(text)
        if card_issues:
            try:
                rel = card_path.relative_to(root_features)
            except ValueError:
                rel = card_path
            hits.append((str(rel), card_issues))
    return hits


def audit_capture_coverage(*, known_sigs: set[str] | None = None) -> MetricScore:
    """C1 — done cards with resolvable promotions / cards with lessons captured."""
    known = known_sigs or _known_signatures()
    lesson_cards = _cards_with_lessons()
    if not lesson_cards:
        return MetricScore("C1 Capture", 0, 0, None, "no done cards with lessons")

    promoted = sum(1 for _, excerpt in lesson_cards if _resolved_card_has_promotion(excerpt, known))
    score = promoted / len(lesson_cards)
    return MetricScore(
        "C1 Capture",
        promoted,
        len(lesson_cards),
        score,
        f"{promoted}/{len(lesson_cards)} cards with resolvable promotions",
    )


def audit_promotion_quality(*, known_sigs: set[str] | None = None) -> MetricScore:
    """C2 — correctly typed refs / total governance refs (skip empty cards)."""
    known = known_sigs or _known_signatures()
    total = 0
    correct = 0
    for _, excerpt in _cards_with_lessons():
        refs = _collect_c2_refs(excerpt)
        if not refs:
            continue
        for ref, source in refs:
            total += 1
            if _ref_is_correctly_typed(ref, source, known):
                correct += 1

    if total == 0:
        return MetricScore("C2 Promotion quality", 0, 0, None, "no governance refs")
    score = correct / total
    return MetricScore(
        "C2 Promotion quality",
        correct,
        total,
        score,
        f"{correct}/{total} correctly typed refs",
    )


def extract_context_done_links(text: str) -> list[Path]:
    """Paths under ``done/`` or ``archived/`` linked from ``## Context``."""
    body_match = re.search(r"^## Context\s*\n", text, re.MULTILINE)
    if not body_match:
        return []
    rest = text[body_match.end() :]
    section = rest.split("\n## ", 1)[0]
    linked: list[Path] = []
    for name in _CONTEXT_CARD_LINK_RE.findall(section):
        for directory in _closed_card_dirs():
            candidate = directory / name
            if candidate.is_file():
                linked.append(candidate)
                break
    return linked


def find_relevant_lesson_cards(
    card_path: Path,
    *,
    strict: bool = False,
) -> list[Path]:
    """Expanded relevance set for C3 (epic, areas, paths, Context links)."""
    text = card_path.read_text(encoding="utf-8")
    meta = _parse_frontmatter(text)
    epic = str(meta.get("epic") or "")
    labels = extract_feature_area_labels(text)
    path_prefixes = extract_label_paths(text)
    context_links = {p.resolve() for p in extract_context_done_links(text)}
    label_set = {label.strip() for label in labels if label.strip()}

    relevant: list[Path] = []
    for closed_path in _iter_closed_cards():
        closed_text = closed_path.read_text(encoding="utf-8")
        if _lessons_excerpt(closed_text) is None:
            continue
        matched = False
        closed_meta = _parse_frontmatter(closed_text)
        card_epic = str(closed_meta.get("epic") or "")
        if not strict and epic and card_epic == epic:
            matched = True
        if label_set and any(label in closed_text for label in label_set):
            matched = True
        if path_prefixes and _path_overlaps(_card_paths_from_text(closed_text), path_prefixes):
            matched = True
        if closed_path.resolve() in context_links:
            matched = True
        if matched:
            relevant.append(closed_path)
    return relevant


def _card_paths_from_text(content: str) -> list[str]:
    paths: list[str] = []
    for line in content.splitlines():
        if line.startswith("- `") and "`" in line[3:]:
            path = line.split("`", 2)[1]
            if "/" in path or path.endswith(".py"):
                paths.append(path)
    return paths


def audit_consumption_coverage(
    card_path: Path,
    *,
    strict: bool = False,
    find_lessons=find_done_lessons,
) -> MetricScore:
    """C3 — surfaced / relevant lesson cards for one active card."""
    text = card_path.read_text(encoding="utf-8")
    meta = _parse_frontmatter(text)
    epic = str(meta.get("epic") or "") or None
    labels = extract_feature_area_labels(text)
    path_prefixes = extract_label_paths(text)

    relevant = find_relevant_lesson_cards(card_path, strict=strict)
    if not relevant:
        return MetricScore(
            "C3 Consumption",
            0,
            0,
            None,
            f"{card_path.name}: no relevant lessons",
        )

    surfaced = find_lessons(
        epic=epic,
        labels=labels,
        path_prefixes=path_prefixes,
        strict=strict,
    )
    surfaced_paths = {path.resolve() for path, _ in surfaced}
    relevant_paths = {path.resolve() for path in relevant}
    overlap = len(surfaced_paths & relevant_paths)
    score = overlap / len(relevant_paths)
    return MetricScore(
        "C3 Consumption",
        overlap,
        len(relevant_paths),
        score,
        f"{card_path.name}: {overlap}/{len(relevant_paths)} surfaced/relevant",
    )


def audit_consumption_aggregate(
    features_dir: Path,
    *,
    strict: bool = False,
    find_lessons=find_done_lessons,
) -> MetricScore:
    """C3 aggregate across active kanban cards."""
    scores: list[float] = []
    per_card: dict[str, MetricScore] = {}
    for card_path in _iter_active_cards(features_dir):
        metric = audit_consumption_coverage(
            card_path,
            strict=strict,
            find_lessons=find_lessons,
        )
        per_card[str(card_path.relative_to(REPO_ROOT))] = metric
        if metric.score is not None:
            scores.append(metric.score)
    if not scores:
        return MetricScore("C3 Consumption", 0, 0, None, "no active cards with relevant lessons")
    avg = sum(scores) / len(scores)
    return MetricScore(
        "C3 Consumption",
        int(round(avg * len(scores))),
        len(scores),
        avg,
        f"avg {avg:.0%} over {len(scores)} active cards",
    )


def _extract_prior_lessons_citations(text: str) -> set[str]:
    return extract_prior_lessons_citations(text)


def _lesson_is_cited(
    card_path: Path,
    lessons_text: str,
    citations: set[str],
) -> bool:
    rel = card_path.name
    if rel in citations or str(card_path) in citations:
        return True
    for sig in extract_signatures(lessons_text):
        if sig in citations:
            return True
    for path in extract_governance_artifacts(lessons_text):
        if path in citations or Path(path).name in citations:
            return True
    return False


def _c4_active_card_context(
    card_path: Path,
    text: str,
    *,
    find_lessons=find_done_lessons,
) -> tuple[list[tuple[Path, str]], set[str]] | None:
    """Surfaced lessons + Prior-lessons citations for one C4-eligible active card."""
    if not extract_label_paths(text):
        return None
    if "## Decisions" not in text and "## Corrective Action" not in text:
        return None
    meta = _parse_frontmatter(text)
    epic = str(meta.get("epic") or "") or None
    labels = extract_feature_area_labels(text)
    path_prefixes = extract_label_paths(text)
    surfaced = find_lessons(
        epic=epic,
        labels=labels,
        path_prefixes=path_prefixes,
    )
    if not surfaced:
        return None
    citations = _extract_prior_lessons_citations(text)
    return surfaced, citations


def _card_has_accepted_c4_cite(
    surfaced: list[tuple[Path, str]],
    citations: set[str],
) -> bool:
    """True when Prior-lessons block cites at least one surfaced lesson."""
    if not citations:
        return False
    return any(
        _lesson_is_cited(lesson_path, excerpt, citations) for lesson_path, excerpt in surfaced
    )


def audit_application_coverage(
    features_dir: Path,
    *,
    find_lessons=find_done_lessons,
) -> MetricScore:
    """C4 aggregate — cited surfaced lessons / total surfaced (advisory)."""
    cited_total = 0
    surfaced_total = 0
    for card_path in _iter_active_cards(features_dir):
        text = card_path.read_text(encoding="utf-8")
        context = _c4_active_card_context(card_path, text, find_lessons=find_lessons)
        if context is None:
            continue
        surfaced, citations = context
        for lesson_path, excerpt in surfaced:
            surfaced_total += 1
            if _lesson_is_cited(lesson_path, excerpt, citations):
                cited_total += 1

    if surfaced_total == 0:
        return MetricScore(
            "C4 Application (aggregate)",
            0,
            0,
            None,
            "no surfaced lessons on active cards",
        )
    score = cited_total / surfaced_total
    return MetricScore(
        "C4 Application (aggregate)",
        cited_total,
        surfaced_total,
        score,
        f"{cited_total}/{surfaced_total} surfaced lessons cited in Prior lessons",
    )


def audit_application_coverage_per_card(
    features_dir: Path,
    *,
    find_lessons=find_done_lessons,
) -> MetricScore:
    """C4 per-card — active cards with accepted Prior-lessons cite / eligible cards."""
    passed = 0
    eligible = 0
    for card_path in _iter_active_cards(features_dir):
        text = card_path.read_text(encoding="utf-8")
        context = _c4_active_card_context(card_path, text, find_lessons=find_lessons)
        if context is None:
            continue
        surfaced, citations = context
        eligible += 1
        if _card_has_accepted_c4_cite(surfaced, citations):
            passed += 1

    if eligible == 0:
        return MetricScore(
            "C4 Application (per-card)",
            0,
            0,
            None,
            "no active cards with surfaced lessons",
        )
    score = passed / eligible
    return MetricScore(
        "C4 Application (per-card)",
        passed,
        eligible,
        score,
        f"{passed}/{eligible} active cards with accepted Prior-lessons cite",
    )


def composite_score(*metrics: MetricScore) -> float | None:
    """Equal weights across scored metrics; N/A metrics count as 100%."""
    values: list[float] = []
    for metric in metrics:
        if metric.score is None:
            values.append(1.0)
        else:
            values.append(metric.score)
    if not values:
        return None
    return sum(values) / len(values)


def build_report(
    features_dir: Path,
    *,
    card: Path | None = None,
    strict: bool = False,
    find_lessons=find_done_lessons,
) -> CoverageReport:
    """Run C1–C4 (+ C1b) and compute composite."""
    known = _known_signatures()
    c1 = audit_capture_coverage(known_sigs=known)
    c1b = audit_forward_feedback_coverage()
    c2 = audit_promotion_quality(known_sigs=known)

    if card is not None:
        c3 = audit_consumption_coverage(card, strict=strict, find_lessons=find_lessons)
        per_card = {str(card.relative_to(REPO_ROOT)): c3}
    else:
        c3 = audit_consumption_aggregate(
            features_dir,
            strict=strict,
            find_lessons=find_lessons,
        )
        per_card = {}

    c4 = audit_application_coverage(features_dir, find_lessons=find_lessons)
    c4_per_card = audit_application_coverage_per_card(
        features_dir,
        find_lessons=find_lessons,
    )
    comp = composite_score(c1, c1b, c2, c3, c4_per_card)
    return CoverageReport(
        c1=c1,
        c1b=c1b,
        c2=c2,
        c3=c3,
        c4=c4,
        c4_per_card=c4_per_card,
        composite=comp,
        per_card_c3=per_card,
    )


def format_metric_line(metric: MetricScore) -> str:
    if metric.score is None:
        return f"{metric.name}: N/A ({metric.detail})"
    pct = metric.score * 100
    return f"{metric.name}: {pct:.1f}% ({metric.numerator}/{metric.denominator} — {metric.detail})"


LESSONS_COVERAGE_DRIFT_PREFIX = "Lessons coverage drift alert:"
DEFAULT_LESSONS_COVERAGE_THRESHOLD = 75.0


def kanban_done_data_available(features_dir: Path) -> bool:
    """True when gitignored done/ or archived/ kanban dirs exist locally."""
    done = features_dir / "done"
    archived = features_dir / "archived"
    return done.is_dir() or archived.is_dir()


def lessons_coverage_drift_severity(composite: float) -> str:
    """Map composite (0–1) to drift severity: critical <60%, else warn."""
    if composite * 100 < 60:
        return "critical"
    return "warn"


def format_lessons_coverage_drift_message(
    report: CoverageReport,
    *,
    threshold: float = DEFAULT_LESSONS_COVERAGE_THRESHOLD,
) -> str:
    if report.composite is None:
        return (
            f"{LESSONS_COVERAGE_DRIFT_PREFIX} composite N/A "
            f"(threshold {threshold:g}%) — no scored sub-metrics"
        )
    composite_pct = report.composite * 100
    breakdown = "; ".join(
        format_metric_line(metric)
        for metric in (
            report.c1,
            report.c1b,
            report.c2,
            report.c3,
            report.c4,
            report.c4_per_card,
        )
    )
    return (
        f"{LESSONS_COVERAGE_DRIFT_PREFIX} composite {composite_pct:.1f}% "
        f"(threshold {threshold:g}%) — {breakdown}"
    )
