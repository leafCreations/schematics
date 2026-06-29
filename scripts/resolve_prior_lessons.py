#!/usr/bin/env python3
"""Surface prior lessons and commit-issue patterns for kanban card review.

SSOT CLI for the prior-lessons gate (Signature: ``governance-index-not-grep``). Agents call this
after ``docs/lessons-index.yaml`` — not broad folder grep on ``done/`` / ``archived/``. Scans
``## Lessons captured`` under ``.devtool/features/done/`` and ``.devtool/features/archived/``.
Used during pre-implementation card review (kanban-markdown § Prior lessons gate).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.resolve_feature_areas import resolve_lesson_pointers

FEATURES_DIR = REPO_ROOT / ".devtool/features"
DONE_DIR = FEATURES_DIR / "done"
ARCHIVED_DIR = FEATURES_DIR / "archived"
REGISTRY_PATH = REPO_ROOT / "docs" / "feature-areas.yaml"

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
_LESSONS_HEADING_RE = re.compile(r"^## Lessons captured[^\n]*\n", re.MULTILINE)


def _parse_frontmatter(text: str) -> dict:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _lessons_excerpt(text: str, *, max_lines: int = 12) -> str | None:
    match = _LESSONS_HEADING_RE.search(text)
    if not match:
        return None
    start = match.end()
    rest = text[start:]
    lines: list[str] = []
    for line in rest.splitlines():
        if line.startswith("## ") and lines:
            break
        lines.append(line)
        if len(lines) >= max_lines:
            lines.append("…")
            break
    body = "\n".join(lines).strip()
    return body or None


def _section_body(text: str, heading: str) -> str | None:
    match = re.search(rf"^## {re.escape(heading)}\s*\n", text, re.MULTILINE)
    if not match:
        return None
    lines: list[str] = []
    for line in text[match.end() :].splitlines():
        if line.startswith("## ") and lines:
            break
        lines.append(line)
    body = "\n".join(lines).strip()
    return body or None


def _section_body_aliases(text: str, headings: tuple[str, ...]) -> str | None:
    """Return the first non-empty ``## heading`` body among *headings*."""
    for heading in headings:
        body = _section_body(text, heading)
        if body is not None:
            return body
    return None


_PATH_SECTION_HEADINGS = ("Product Paths", "Label Paths")


def _tests_files_body(text: str) -> str | None:
    """Body under ``### Files`` inside ``## Tests``."""
    tests = _section_body(text, "Tests")
    if tests is None:
        return None
    match = re.search(r"^### Files\s*\n(.*?)(?=^### |\Z)", tests, re.MULTILINE | re.DOTALL)
    if not match:
        return None
    body = match.group(1).strip()
    return body or None


def _card_paths(content: str) -> list[str]:
    paths: list[str] = []
    for line in content.splitlines():
        if line.startswith("- `") and "`" in line[3:]:
            path = line.split("`", 2)[1]
            if "/" in path or path.endswith(".py"):
                paths.append(path)
    return paths


def extract_label_paths(text: str) -> list[str]:
    """Paths from Product/Label Paths and Tests → Files on a kanban card."""
    paths: list[str] = []
    seen: set[str] = set()
    for heading in _PATH_SECTION_HEADINGS:
        body = _section_body(text, heading)
        if body is None:
            continue
        for path in _card_paths(body):
            if path not in seen:
                seen.add(path)
                paths.append(path)
    files_body = _tests_files_body(text)
    if files_body:
        for path in _card_paths(files_body):
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def extract_feature_area_labels(text: str) -> list[str]:
    """Feature area labels from ``## Feature Area`` or ``## Feature Areas``."""
    labels: list[str] = []
    seen: set[str] = set()
    for heading in ("Feature Areas", "Feature Area"):
        body = _section_body(text, heading)
        if body is None:
            continue
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            match = re.search(r"`([^`]+)`", stripped)
            candidate = match.group(1).strip() if match else stripped.lstrip("- ").strip()
            if candidate and candidate not in seen:
                seen.add(candidate)
                labels.append(candidate)
    return labels


_SIGNATURE_PATTERNS = (
    re.compile(r"Signature[`:\s(]+`([^`]+)`"),
    re.compile(r"^\s*-\s*\*\*`([^`]+)`:\*\*", re.MULTILINE),
    re.compile(r"`sig:([^`]+)`"),
)

# Parser SSOT for C4 / coverage lib — stops at ``\n## `` only (not ``\n**`` mid-block).
PRIOR_LESSONS_RE = re.compile(
    r"\*\*Prior lessons(?: \([^)]+\))?:\*\*\s*(.+?)(?=\n## |\Z)",
    re.DOTALL,
)

_CITATION_SIG_RE = re.compile(r"`([a-z][a-z0-9-]+)`")
_CITATION_MD_RE = re.compile(r"`([\w.-]+\.md)`")
_CITATION_PATH_RE = re.compile(r"`((?:[\w./-]+/[\w./-]+|\w+\.mdc))`")
_CITATION_DATED_STEM_RE = re.compile(r"([\w-]+-\d{4}-\d{2}-\d{2}(?:T[\d]+)?\.md)")
_CITATION_DRIFT_STEM_RE = re.compile(r"(governance-drift-registry-[a-f0-9]+\.md)")


def extract_prior_lessons_citations(text: str) -> set[str]:
    """Accepted cite tokens from ``**Prior lessons (YYYY-MM-DD):**`` block."""
    citations: set[str] = set()
    match = PRIOR_LESSONS_RE.search(text)
    if not match:
        return citations
    block = match.group(1)
    for pattern in (
        _CITATION_SIG_RE,
        _CITATION_MD_RE,
        _CITATION_PATH_RE,
        _CITATION_DATED_STEM_RE,
        _CITATION_DRIFT_STEM_RE,
    ):
        for path_match in pattern.finditer(block):
            citations.add(path_match.group(1))
    return citations


def extract_signatures(text: str) -> list[str]:
    """Promotion Signatures from card prose and ``sig:`` artifacts entries."""
    found: list[str] = []
    seen: set[str] = set()
    for sig in _collect_parsed_artifacts(text).signatures:
        if sig not in seen:
            seen.add(sig)
            found.append(sig)
    for pattern in _SIGNATURE_PATTERNS:
        for match in pattern.finditer(text):
            sig = match.group(1).strip()
            if sig and sig not in seen:
                seen.add(sig)
                found.append(sig)
    return found


_ARTIFACT_SUFFIXES = (".md", ".mdc", ".yaml")
_LINK_PATH_RE = re.compile(r"\]\(([^)]+)\)")
_BACKTICK_PATH_RE = re.compile(r"`((?:\.cursor/|docs/|AGENTS\.md)[^`]+)`")
_ARTIFACTS_BULLET_RE = re.compile(r"^\s*-\s*artifacts:\s*(.+)$", re.IGNORECASE)


@dataclass
class ParsedArtifacts:
    """Typed entries from one ``artifacts:`` sub-bullet on a lesson capture."""

    skills: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    docs: list[str] = field(default_factory=list)
    signatures: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)

    def repo_paths(self) -> list[str]:
        """Indexable repo paths (skills, rules, docs, tests — not signatures)."""
        seen: set[str] = set()
        ordered: list[str] = []
        for path in self.skills + self.rules + self.docs + self.tests:
            if path not in seen:
                seen.add(path)
                ordered.append(path)
        return ordered


def _normalize_skill_ref(value: str) -> str | None:
    value = value.strip()
    if value.startswith(".cursor/skills/"):
        return value if value.endswith("SKILL.md") else None
    skill_name = value.split("/", 1)[0].strip()
    if not skill_name:
        return None
    return f".cursor/skills/{skill_name}/SKILL.md"


def _normalize_rule_ref(value: str) -> str | None:
    path = value.split("#", 1)[0].strip()
    if path.startswith(".cursor/rules/"):
        return path if path.endswith(".mdc") else None
    if path.endswith(".mdc"):
        return f".cursor/rules/{path}"
    return None


_REGISTRY_YAML_STEMS = frozenset({"lessons-index", "feature-areas"})


def _normalize_doc_ref(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    if value.startswith("docs/"):
        return value
    if value.endswith((".md", ".yaml", ".yml")):
        return f"docs/{value}"
    if value in _REGISTRY_YAML_STEMS:
        return None
    return f"docs/{value}.md"


def _normalize_test_ref(value: str) -> str | None:
    value = value.strip()
    if value.startswith("tests/"):
        return value if value.endswith(".py") else None
    if value.endswith(".py"):
        return value if "/" in value else f"tests/{value}"
    return None


def _parse_artifact_entry(entry: str) -> tuple[str, str] | None:
    entry = entry.strip()
    if ":" not in entry:
        return None
    prefix, _, raw = entry.partition(":")
    prefix = prefix.lower().strip()
    value = raw.strip()
    if not value:
        return None
    if prefix == "sig":
        return ("sig", value)
    normalizers = {
        "skill": _normalize_skill_ref,
        "rule": _normalize_rule_ref,
        "doc": _normalize_doc_ref,
        "test": _normalize_test_ref,
    }
    normalizer = normalizers.get(prefix)
    if normalizer is None:
        return None
    normalized = normalizer(value)
    if not normalized:
        return None
    return (prefix, normalized)


def parse_artifacts_line(line: str) -> ParsedArtifacts:
    """Parse one ``artifacts:`` sub-bullet (comma-separated typed entries)."""
    match = _ARTIFACTS_BULLET_RE.match(line)
    parsed = ParsedArtifacts()
    if not match:
        return parsed
    for entry in match.group(1).split(","):
        item = _parse_artifact_entry(entry)
        if item is None:
            continue
        kind, value = item
        bucket = getattr(parsed, f"{kind}s" if kind != "sig" else "signatures")
        if value not in bucket:
            bucket.append(value)
    return parsed


def _collect_parsed_artifacts(lessons_text: str) -> ParsedArtifacts:
    combined = ParsedArtifacts()
    for line in lessons_text.splitlines():
        parsed = parse_artifacts_line(line)
        for field_name in ("skills", "rules", "docs", "signatures", "tests"):
            bucket = getattr(combined, field_name)
            for value in getattr(parsed, field_name):
                if value not in bucket:
                    bucket.append(value)
    return combined


def _normalize_artifact_path(raw: str) -> str | None:
    path = raw.strip()
    while path.startswith("../"):
        path = path[3:]
    if path == "AGENTS.md":
        return path
    if path.endswith(_ARTIFACT_SUFFIXES) or path.endswith("SKILL.md"):
        return path
    return None


def extract_governance_artifacts(lessons_text: str) -> list[str]:
    """Repo paths from ``artifacts:`` sub-bullets, else ``**Governance:**`` links."""
    parsed = _collect_parsed_artifacts(lessons_text)
    if parsed.repo_paths():
        return parsed.repo_paths()

    artifacts: list[str] = []
    seen: set[str] = set()
    for line in lessons_text.splitlines():
        if "overnance:" not in line:
            continue
        for pattern in (_LINK_PATH_RE, _BACKTICK_PATH_RE):
            for match in pattern.finditer(line):
                normalized = _normalize_artifact_path(match.group(1))
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    artifacts.append(normalized)
    return artifacts


def _path_overlaps(card_paths: list[str], prefixes: list[str]) -> bool:
    if not prefixes:
        return False
    for path in card_paths:
        for prefix in prefixes:
            if path == prefix or path.startswith(prefix.rstrip("/") + "/"):
                return True
            if prefix in path:
                return True
    return False


def _closed_card_dirs() -> list[Path]:
    """Directories for completed kanban cards (user-managed)."""
    dirs: list[Path] = []
    for path in (DONE_DIR, ARCHIVED_DIR):
        if path.is_dir():
            dirs.append(path)
    return dirs


def _iter_cards(*, closed_only: bool) -> list[Path]:
    if closed_only:
        paths: list[Path] = []
        for directory in _closed_card_dirs():
            paths.extend(directory.glob("*.md"))
        return sorted(paths)
    if not FEATURES_DIR.is_dir():
        return []
    paths = list(FEATURES_DIR.glob("*.md"))
    for directory in _closed_card_dirs():
        paths.extend(directory.glob("*.md"))
    return sorted(paths)


def find_done_lessons(
    *,
    epic: str | None,
    labels: list[str],
    path_prefixes: list[str],
    strict: bool = False,
) -> list[tuple[Path, str]]:
    """Match ``## Lessons captured`` on cards under ``done/`` and ``archived/``."""
    if strict:
        return find_done_lessons_strict(
            epic=epic,
            labels=labels,
            path_prefixes=path_prefixes,
        )
    hits: list[tuple[Path, str]] = []
    label_set = {label.strip() for label in labels if label.strip()}

    for card_path in _iter_cards(closed_only=True):
        text = card_path.read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        card_epic = str(meta.get("epic") or "")
        lessons = _lessons_excerpt(text)
        if lessons is None:
            continue

        matched = False
        if epic and card_epic == epic:
            matched = True
        if label_set and any(label in text for label in label_set):
            matched = True
        if path_prefixes and _path_overlaps(_card_paths(text), path_prefixes):
            matched = True

        if matched:
            hits.append((card_path, lessons))

    return hits


def find_done_lessons_strict(
    *,
    epic: str | None,
    labels: list[str],
    path_prefixes: list[str],
) -> list[tuple[Path, str]]:
    """Like ``find_done_lessons`` but epic alone does not match."""
    del epic  # epic-only match disabled; labels or path overlap required
    hits: list[tuple[Path, str]] = []
    label_set = {label.strip() for label in labels if label.strip()}

    for card_path in _iter_cards(closed_only=True):
        text = card_path.read_text(encoding="utf-8")
        lessons = _lessons_excerpt(text)
        if lessons is None:
            continue

        matched = False
        if label_set and any(label in text for label in label_set):
            matched = True
        if path_prefixes and _path_overlaps(_card_paths(text), path_prefixes):
            matched = True

        if matched:
            hits.append((card_path, lessons))

    return hits


def find_commit_issue_cards(path_prefixes: list[str]) -> list[tuple[Path, str]]:
    hits: list[tuple[Path, str]] = []
    for card_path in _iter_cards(closed_only=False):
        text = card_path.read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        labels = meta.get("labels") or []
        if "commit-issue" not in labels:
            continue
        status = str(meta.get("status") or "")
        if status == "done":
            continue
        card_paths = _card_paths(text)
        if (
            path_prefixes
            and not _path_overlaps(card_paths, path_prefixes)
            and not _path_overlaps(
                [line for line in text.splitlines() if "/" in line],
                path_prefixes,
            )
        ):
            continue
        problem = ""
        if "## Problem" in text:
            start = text.index("## Problem")
            chunk = text[start : start + 600]
            problem = chunk.split("\n## ", 1)[0].strip()
        hits.append((card_path, problem or "(see card Problem / Failed Tests)"))
    return hits


def area_artifacts(labels: list[str]) -> dict[str, list[str]]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    areas = data.get("areas", {})
    out: dict[str, list[str]] = {"docs": [], "related": []}
    seen_docs: set[str] = set()
    seen_related: set[str] = set()
    for label in labels:
        entry = areas.get(label)
        if not entry:
            continue
        for doc in entry.get("docs", []) or []:
            if doc not in seen_docs:
                seen_docs.add(doc)
                out["docs"].append(doc)
        for related in entry.get("related", []) or []:
            if related not in seen_related:
                seen_related.add(related)
                out["related"].append(related)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epic", help="Card epic slug (e.g. RenderEngine)")
    parser.add_argument(
        "labels",
        nargs="*",
        help="Feature area labels (e.g. 'Render Preview')",
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        default=[],
        help="Path prefixes for commit-issue / done-card overlap (optional)",
    )
    parser.add_argument(
        "--audit",
        choices=("capture", "application", "all"),
        help="Run lessons coverage audit (delegates to check_lessons_coverage)",
    )
    args = parser.parse_args(argv)

    if args.audit:
        from scripts.check_lessons_coverage import run_audit

        mode = None if args.audit == "all" else args.audit
        return run_audit(mode=mode)

    labels = list(args.labels)
    path_prefixes = list(args.paths or [])

    print("# Prior lessons gate\n")

    lessons = find_done_lessons(
        epic=args.epic,
        labels=labels,
        path_prefixes=path_prefixes,
    )
    if lessons:
        print("## Done and archived cards — Lessons captured\n")
        for card_path, excerpt in lessons:
            rel = card_path.relative_to(REPO_ROOT)
            print(f"### {rel}\n")
            print(excerpt)
            print()
    else:
        print("## Done and archived cards — Lessons captured\n")
        print("(none matched epic / feature areas / paths)\n")

    commit_issues = find_commit_issue_cards(path_prefixes)
    if commit_issues:
        print("## Open commit-issue cards\n")
        for card_path, problem in commit_issues:
            rel = card_path.relative_to(REPO_ROOT)
            print(f"- `{rel}` — {problem[:200]}")
        print()

    if labels:
        pointers, pointer_unknown = resolve_lesson_pointers(labels)
        if pointer_unknown:
            print(
                "Unknown labels (lesson pointers):",
                ", ".join(pointer_unknown),
                file=sys.stderr,
            )
        if pointers["lesson_signatures"] or pointers["lesson_docs"]:
            print("## Registry lesson pointers\n")
            if pointers["lesson_signatures"]:
                print("### Signatures\n")
                for sig in pointers["lesson_signatures"]:
                    print(f"- `{sig}`")
                print()
            if pointers["lesson_docs"]:
                print("### Docs\n")
                for doc in pointers["lesson_docs"]:
                    print(f"- `{doc}`")
                print()

        artifacts = area_artifacts(labels)
        if artifacts["docs"]:
            print("## Feature area docs (read before Decisions)\n")
            for doc in artifacts["docs"]:
                print(f"- `{doc}`")
            print()
        if artifacts["related"]:
            print("## Related feature areas\n")
            for related in artifacts["related"]:
                print(f"- `{related}`")
            print()

    print("## Grep Signatures (agent-triage §1b)\n")
    print("- `rg 'Signature:' .cursor/rules/testing.mdc`")
    print("- `rg '|' .cursor/skills/pre-commit-workflow/reference.md` (Failure patterns)")
    print("- `rg '|' .cursor/skills/agent-self-evaluation/reference.md` (Common failure)")
    print("- Area skills: AGENTS.md § Area → skills & rules for resolved labels")
    print()
    print("Record applied lessons in **Decisions** / **Corrective Action** (bullet per lesson).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
