"""Tests for lessons coverage audit (C1–C4)."""

from __future__ import annotations

from pathlib import Path

import pytest

import scripts.lessons_coverage_lib as lib
import scripts.resolve_prior_lessons as rpl
from scripts.check_lessons_coverage import report_to_dict, run_audit
from scripts.lessons_coverage_lib import (
    audit_application_coverage,
    audit_capture_coverage,
    audit_consumption_coverage,
    audit_promotion_quality,
    build_report,
    composite_score,
    extract_context_done_links,
)
from scripts.resolve_prior_lessons import (
    find_done_lessons,
    find_done_lessons_strict,
    parse_artifacts_line,
)


@pytest.fixture
def kanban_dirs(tmp_path, monkeypatch):
    """Point kanban dirs at tmp_path fixtures."""
    features = tmp_path / "features"
    done = features / "done"
    archived = features / "archived"
    done.mkdir(parents=True)
    archived.mkdir(parents=True)
    monkeypatch.setattr(rpl, "FEATURES_DIR", features)
    monkeypatch.setattr(rpl, "DONE_DIR", done)
    monkeypatch.setattr(rpl, "ARCHIVED_DIR", archived)
    return features, done, archived


def _write_done(done_dir: Path, name: str, body: str, *, epic: str = "TestEpic") -> Path:
    card = done_dir / name
    card.write_text(f"---\nepic: {epic}\n---\n\n{body}", encoding="utf-8")
    return card


def test_parse_artifacts_line_typed_entries():
    line = (
        "  - artifacts: skill:project-context, "
        "rule:testing.mdc#orbit-animated-texture-strip, sig:orbit-animated-texture-strip"
    )
    parsed = parse_artifacts_line(line)
    assert parsed.skills == [".cursor/skills/project-context/SKILL.md"]
    assert parsed.rules == [".cursor/rules/testing.mdc"]
    assert parsed.signatures == ["orbit-animated-texture-strip"]


def test_c2_artifacts_counted_correct(kanban_dirs, monkeypatch):
    _, done, _ = kanban_dirs
    known = {"governance-compact-baseline", "orbit-animated-texture-strip"}
    monkeypatch.setattr(lib, "_known_signatures", lambda: known)
    monkeypatch.setattr(lib, "_path_exists", lambda _path: True)

    _write_done(
        done,
        "with-artifacts.md",
        "## Lessons captured (2026-06-27)\n\n"
        "- **Fix:** use frame 0.\n"
        "  - artifacts: skill:agent-triage, rule:agent-consistency.mdc, "
        "sig:governance-compact-baseline, test:tests/test_check_governance_parity.py\n",
    )

    metric = audit_promotion_quality(known_sigs=known)
    assert metric.score == 1.0
    assert metric.denominator == 4


def test_c2_heuristic_governance_paths(kanban_dirs, monkeypatch):
    _, done, _ = kanban_dirs
    known: set[str] = set()
    monkeypatch.setattr(lib, "_known_signatures", lambda: known)
    monkeypatch.setattr(lib, "_path_exists", lambda path: path.startswith(".cursor/"))

    _write_done(
        done,
        "heuristic.md",
        "## Lessons captured (2026-06-27)\n\n"
        "- **Governance:** "
        "[agent-triage](.cursor/skills/agent-triage/SKILL.md), "
        "`docs/development.md`\n",
    )

    metric = audit_promotion_quality(known_sigs=known)
    assert metric.score == 1.0
    assert metric.denominator == 2


def test_c1_capture_counts_promoted_cards(kanban_dirs, monkeypatch):
    _, done, _ = kanban_dirs
    known = {"governance-compact-baseline"}
    monkeypatch.setattr(lib, "_known_signatures", lambda: known)
    monkeypatch.setattr(lib, "_path_exists", lambda _path: True)

    _write_done(
        done,
        "promoted.md",
        "## Lessons captured (2026-06-27)\n\n"
        "- **Fix:** baseline.\n"
        "  - artifacts: sig:governance-compact-baseline\n",
    )
    _write_done(
        done,
        "empty-lesson.md",
        "## Lessons captured (2026-06-27)\n\n- **Note:** no governance links.\n",
    )

    metric = audit_capture_coverage(known_sigs=known)
    assert metric.numerator == 1
    assert metric.denominator == 2
    assert metric.score == 0.5


def test_find_done_lessons_strict_skips_epic_only(kanban_dirs):
    _, done, _ = kanban_dirs
    _write_done(
        done,
        "epic-only.md",
        "## Lessons captured (2026-06-27)\n\n- epic matched lesson\n",
        epic="SharedEpic",
    )

    loose = find_done_lessons(epic="SharedEpic", labels=[], path_prefixes=[])
    strict = find_done_lessons_strict(epic="SharedEpic", labels=[], path_prefixes=[])
    assert len(loose) == 1
    assert len(strict) == 0


def test_find_done_lessons_strict_matches_paths(kanban_dirs):
    _, done, _ = kanban_dirs
    _write_done(
        done,
        "path-match.md",
        "## Label Paths\n\n- `scripts/check_lessons_coverage.py`\n\n"
        "## Lessons captured (2026-06-27)\n\n- path overlap lesson\n",
    )

    hits = find_done_lessons_strict(
        epic=None,
        labels=[],
        path_prefixes=["scripts/check_lessons_coverage.py"],
    )
    assert len(hits) == 1


def test_c4_application_coverage_prior_lessons(kanban_dirs, monkeypatch):
    features, done, _ = kanban_dirs
    monkeypatch.setattr(lib, "_known_signatures", lambda: {"app-lesson-sig"})

    _write_done(
        done,
        "surfaced-lesson.md",
        "## Label Paths\n\n- `scripts/foo.py`\n\n"
        "## Lessons captured (2026-06-27)\n\n"
        "- **Fix:** cite in Prior lessons.\n"
        "  - artifacts: sig:app-lesson-sig\n",
        epic="AppEpic",
    )

    active = features / "review-with-prior.md"
    active.write_text(
        "---\nstatus: review\nepic: AppEpic\n---\n\n"
        "## Feature Area\n\n`Agent Workflow`\n\n"
        "## Label Paths\n\n- `scripts/foo.py`\n\n"
        "## Decisions\n\n"
        "**Prior lessons (2026-06-27):** "
        "Applied `surfaced-lesson.md` — Signature `app-lesson-sig`.\n",
        encoding="utf-8",
    )

    metric = audit_application_coverage(features)
    assert metric.score == 1.0
    assert metric.numerator == 1
    assert metric.denominator == 1


def test_extract_prior_lessons_citations_commit_issue_and_hash_ids():
    text = (
        "## Decisions\n\n"
        "**Prior lessons (2026-06-27):** commit-issue-pytest-2026-06-25T015348.md, "
        "governance-drift-registry-dd7c222873.md, `lessons-coverage-metric-spec-2026-06-25.md`.\n"
    )
    cites = lib._extract_prior_lessons_citations(text)
    assert "commit-issue-pytest-2026-06-25T015348.md" in cites
    assert "governance-drift-registry-dd7c222873.md" in cites
    assert "lessons-coverage-metric-spec-2026-06-25.md" in cites


def test_resolve_prior_lessons_audit_all_empty_fixture(kanban_dirs, monkeypatch):
    features, _, _ = kanban_dirs
    import scripts.check_lessons_coverage as clc

    monkeypatch.setattr(rpl, "FEATURES_DIR", features)
    monkeypatch.setattr(clc, "FEATURES_DIR", features)

    assert rpl.main(["--audit", "all"]) == 0


def test_c3_card_consumption(kanban_dirs, monkeypatch):
    features, done, _ = kanban_dirs
    known: set[str] = set()
    monkeypatch.setattr(lib, "_known_signatures", lambda: known)

    _write_done(
        done,
        "done-lesson.md",
        "## Feature Area\n\n`Agent Workflow`\n\n"
        "## Lessons captured (2026-06-27)\n\n- lesson body\n",
        epic="LessonsCoverageMetric",
    )

    active = features / "active-card.md"
    active.write_text(
        "---\nstatus: in-progress\nepic: LessonsCoverageMetric\n---\n\n"
        "## Feature Area\n\n`Agent Workflow`\n\n"
        "## Label Paths\n\n- `scripts/check_lessons_coverage.py`\n",
        encoding="utf-8",
    )

    metric = audit_consumption_coverage(active, strict=False)
    assert metric.score is not None
    assert metric.numerator >= 1
    assert metric.denominator >= 1


def test_c3_strict_excludes_epic_only_relevant(kanban_dirs, monkeypatch):
    features, done, _ = kanban_dirs
    monkeypatch.setattr(lib, "_known_signatures", lambda: set())

    _write_done(
        done,
        "epic-lesson.md",
        "## Lessons captured (2026-06-27)\n\n- epic only\n",
        epic="OnlyEpic",
    )

    active = features / "review-card.md"
    active.write_text(
        "---\nstatus: review\nepic: OnlyEpic\n---\n\n## Feature Area\n\n`Agent Workflow`\n\n",
        encoding="utf-8",
    )

    loose = audit_consumption_coverage(active, strict=False)
    strict = audit_consumption_coverage(active, strict=True)
    assert loose.score is not None
    assert strict.score is None or strict.denominator == 0


def test_extract_context_done_links(kanban_dirs):
    features, done, _ = kanban_dirs
    _write_done(done, "context-target.md", "## Lessons captured\n\n- ctx\n")

    card = features / "with-context.md"
    card.write_text(
        "## Context\n\nSee [parent](done/context-target.md).\n",
        encoding="utf-8",
    )
    links = extract_context_done_links(card.read_text(encoding="utf-8"))
    assert any(path.name == "context-target.md" for path in links)


def test_composite_equal_weights():
    from scripts.lessons_coverage_lib import MetricScore

    c1 = MetricScore("C1", 1, 1, 1.0)
    c2 = MetricScore("C2", 1, 2, 0.5)
    c3 = MetricScore("C3", 0, 0, None)
    c4 = MetricScore("C4", 1, 4, 0.25)
    assert composite_score(c1, c2, c3, c4) == pytest.approx(0.6875)


def test_build_report_json(kanban_dirs, monkeypatch):
    features, done, _ = kanban_dirs
    monkeypatch.setattr(lib, "_known_signatures", lambda: {"governance-compact-baseline"})
    monkeypatch.setattr(lib, "_path_exists", lambda _path: True)

    _write_done(
        done,
        "sample.md",
        "## Lessons captured (2026-06-27)\n\n"
        "- **Fix:** doc.\n"
        "  - artifacts: sig:governance-compact-baseline\n",
    )

    report = build_report(features)
    data = report_to_dict(report)
    assert data["c1"]["score_pct"] is not None
    assert data["c2"]["score_pct"] is not None
    assert data["composite_pct"] is not None


def test_run_audit_exit_code_below_threshold(kanban_dirs, monkeypatch, tmp_path):
    features, done, _ = kanban_dirs
    monkeypatch.setattr(lib, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(rpl, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(lib, "_known_signatures", lambda: set())
    monkeypatch.setattr(lib, "_path_exists", lambda _path: False)

    _write_done(
        done,
        "uncited-lesson.md",
        "## Lessons captured (2026-06-27)\n\n- lesson without promotion\n",
        epic="CoverageEpic",
    )

    active = features / "active-card.md"
    active.write_text(
        "---\nstatus: review\nepic: CoverageEpic\n---\n\n"
        "## Feature Area\n\n`Agent Workflow`\n\n"
        "## Label Paths\n\n- `scripts/foo.py`\n\n"
        "## Decisions\n\n- TBD\n",
        encoding="utf-8",
    )

    import scripts.check_lessons_coverage as clc

    monkeypatch.setattr(clc, "FEATURES_DIR", features)
    assert run_audit(threshold=75.0) == 1


def test_run_audit_exit_code_at_threshold(kanban_dirs, monkeypatch):
    features, _, _ = kanban_dirs
    import scripts.check_lessons_coverage as clc

    monkeypatch.setattr(clc, "FEATURES_DIR", features)
    assert run_audit(threshold=75.0) == 0


def test_rpl_parse_artifacts_doc_and_skill():
    line = "  - artifacts: doc:development.md, skill:agent-triage"
    parsed = parse_artifacts_line(line)
    assert parsed.docs == ["docs/development.md"]
    assert parsed.skills == [".cursor/skills/agent-triage/SKILL.md"]
