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
    extract_signatures,
    find_done_lessons,
    parse_artifacts_line,
)

_SIGNATURE_TABLE_PATHS = (
    REPO_ROOT / ".cursor/skills/pre-commit-workflow/reference.md",
    REPO_ROOT / ".cursor/skills/agent-self-evaluation/reference.md",
)

_ACTIVE_STATUSES = frozenset({"todo", "in-progress", "review"})
_PRIOR_LESSONS_RE = re.compile(
    r"\*\*Prior lessons(?: \([^)]+\))?:\*\*\s*(.+?)(?=\n\*\*|\n## |\Z)",
    re.DOTALL,
)
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
    """Full C1–C4 audit output."""

    c1: MetricScore
    c2: MetricScore
    c3: MetricScore
    c4: MetricScore
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
    citations: set[str] = set()
    match = _PRIOR_LESSONS_RE.search(text)
    if not match:
        return citations
    block = match.group(1)
    for sig_match in re.finditer(r"`([a-z][a-z0-9-]+)`", block):
        citations.add(sig_match.group(1))
    for path_match in re.finditer(r"`([\w.-]+\.md)`", block):
        citations.add(path_match.group(1))
    for path_match in re.finditer(r"`((?:[\w./-]+/[\w./-]+|\w+\.mdc))`", block):
        citations.add(path_match.group(1))
    for path_match in re.finditer(
        r"([\w-]+-\d{4}-\d{2}-\d{2}(?:T[\d]+)?\.md)",
        block,
    ):
        citations.add(path_match.group(1))
    for path_match in re.finditer(
        r"(governance-drift-registry-[a-f0-9]+\.md)",
        block,
    ):
        citations.add(path_match.group(1))
    return citations


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


def audit_application_coverage(
    features_dir: Path,
    *,
    find_lessons=find_done_lessons,
) -> MetricScore:
    """C4 — Prior lessons citations / surfaced lessons on active cards."""
    cited_total = 0
    surfaced_total = 0
    for card_path in _iter_active_cards(features_dir):
        text = card_path.read_text(encoding="utf-8")
        if not extract_label_paths(text):
            continue
        if "## Decisions" not in text and "## Corrective Action" not in text:
            continue
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
            continue
        citations = _extract_prior_lessons_citations(text)
        for lesson_path, excerpt in surfaced:
            surfaced_total += 1
            if _lesson_is_cited(lesson_path, excerpt, citations):
                cited_total += 1

    if surfaced_total == 0:
        return MetricScore("C4 Application", 0, 0, None, "no surfaced lessons on active cards")
    score = cited_total / surfaced_total
    return MetricScore(
        "C4 Application",
        cited_total,
        surfaced_total,
        score,
        f"{cited_total}/{surfaced_total} surfaced lessons cited in Prior lessons",
    )


def composite_score(*metrics: MetricScore) -> float | None:
    """Equal 0.25 weights; N/A metrics count as 100%."""
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
    """Run C1–C4 and compute composite."""
    known = _known_signatures()
    c1 = audit_capture_coverage(known_sigs=known)
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
    comp = composite_score(c1, c2, c3, c4)
    return CoverageReport(
        c1=c1,
        c2=c2,
        c3=c3,
        c4=c4,
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
        format_metric_line(metric) for metric in (report.c1, report.c2, report.c3, report.c4)
    )
    return (
        f"{LESSONS_COVERAGE_DRIFT_PREFIX} composite {composite_pct:.1f}% "
        f"(threshold {threshold:g}%) — {breakdown}"
    )
