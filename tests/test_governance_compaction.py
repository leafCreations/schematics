"""Tests for governance compaction drift (Signature: governance-compaction-drift-alert)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_governance_parity import (
    PREFIX_COMPACTION,
    PREFIX_DUPLICATION,
    run_compaction_audit,
    run_duplication_threshold_audit,
)
from scripts.governance_compaction_lib import (
    CLASSIFY_TRIO_SUM_LABEL,
    KANBAN_LIFECYCLE_SUM_LABEL,
    SEVERITY_CRITICAL,
    SEVERITY_WARN,
    compaction_drift_lines,
    compare_duplication_count_to_threshold,
    compute_duplication_aggregates,
    duplication_threshold_lines,
    evaluate_compaction_drift,
    evaluate_duplication_thresholds,
    load_compaction_baseline,
)


def _write_baseline(repo: Path, *, gc0_total: int = 100, gov_lines: int = 50) -> None:
    gov_dir = repo / "docs" / "governance"
    gov_dir.mkdir(parents=True)
    (gov_dir / "compaction-baseline.yaml").write_text(
        f"""captured_at: "2026-06-27"
gc0_total_lines: {gc0_total}
always_on_governance_lines: {gov_lines}
always_on_total_lines: 80
thresholds:
  gc0_total_warn_pct: 15
  gc0_total_critical_pct: 25
  always_on_governance_warn_lines: 400
  always_on_governance_critical_lines: 480
  per_artifact_warn_pct: 20
  per_artifact_critical_pct: 50
  per_artifact_warn_absolute: 600
  per_artifact_critical_absolute: 900
  duplication_reference_warn: 700
  duplication_reference_critical: 1000
  duplication_kanban_rules_warn: 600
  duplication_kanban_rules_critical: 800
  classify_trio_warn: 80
  classify_trio_critical: 120
  kanban_lifecycle_warn: 900
  kanban_lifecycle_critical: 1200
per_artifact:
  AGENTS.md: 10
duplication_pairs:
  kanban-markdown reference: 20
  kanban-*.mdc (sum): 15
  classify trio (sum): 10
  kanban lifecycle (sum): 35
""",
        encoding="utf-8",
    )


def _minimal_gc0_repo(repo: Path, *, agents_lines: int = 10) -> None:
    (repo / "AGENTS.md").write_text("x\n" * agents_lines, encoding="utf-8")
    rules = repo / ".cursor" / "rules"
    rules.mkdir(parents=True)
    (rules / "agent-routing.mdc").write_text(
        "---\nalwaysApply: true\n---\n" + "r\n" * 5,
        encoding="utf-8",
    )
    (rules / "kanban-card-gates.mdc").write_text(
        "---\nalwaysApply: true\n---\n" + "k\n" * 3,
        encoding="utf-8",
    )
    skills = repo / ".cursor" / "skills" / "agent-triage"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("# triage\n", encoding="utf-8")
    (skills / "reference.md").write_text("# ref\n", encoding="utf-8")
    kanban = repo / ".cursor" / "skills" / "kanban-markdown"
    kanban.mkdir(parents=True)
    (kanban / "SKILL.md").write_text("# kanban\n", encoding="utf-8")
    (kanban / "reference.md").write_text("# ref\n", encoding="utf-8")
    self_eval = repo / ".cursor" / "skills" / "agent-self-evaluation"
    self_eval.mkdir(parents=True)
    (self_eval / "SKILL.md").write_text("# self\n", encoding="utf-8")
    (rules / "kanban-bug-cards.mdc").write_text("bug\n", encoding="utf-8")


def test_load_compaction_baseline_reads_yaml(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_baseline(repo)
    data = load_compaction_baseline(repo)
    assert data["gc0_total_lines"] == 100


def test_evaluate_compaction_ok_when_below_warn(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_baseline(repo, gc0_total=1000, gov_lines=50)
    _minimal_gc0_repo(repo, agents_lines=10)
    report = evaluate_compaction_drift(repo)
    assert report.severity not in {SEVERITY_WARN, SEVERITY_CRITICAL}


def test_compaction_drift_lines_warn_when_gc0_exceeds_threshold(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_baseline(repo, gc0_total=10, gov_lines=5)
    _minimal_gc0_repo(repo, agents_lines=50)
    lines = compaction_drift_lines(repo, include_severity=True)
    assert len(lines) == 1
    assert PREFIX_COMPACTION in lines[0]
    assert "[warn]" in lines[0] or "[critical]" in lines[0]


def test_compaction_drift_critical_on_large_reference(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_baseline(repo)
    _minimal_gc0_repo(repo)
    ref = repo / ".cursor" / "skills" / "kanban-markdown" / "reference.md"
    ref.write_text("line\n" * 950, encoding="utf-8")
    report = evaluate_compaction_drift(repo)
    assert report.severity == SEVERITY_CRITICAL


def test_main_compaction_exits_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_baseline(repo, gc0_total=10, gov_lines=5)
    _minimal_gc0_repo(repo, agents_lines=40)
    features = repo / ".devtool" / "features"
    features.mkdir(parents=True)
    from scripts import check_governance_parity as mod

    code = mod.main(["--repo-root", str(repo), "--compaction", "--no-spawn-cards"])
    captured = capsys.readouterr()
    assert code == 0
    assert PREFIX_COMPACTION in captured.out


def test_compaction_spawn_skipped_on_warn_only(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_baseline(repo, gc0_total=100, gov_lines=50)
    _minimal_gc0_repo(repo, agents_lines=12)
    features = repo / ".devtool" / "features"
    features.mkdir(parents=True)
    report = evaluate_compaction_drift(repo)
    assert report.severity == SEVERITY_WARN
    run_compaction_audit(
        repo_root=repo,
        features_dir=features,
        quiet=True,
        spawn_cards=True,
    )
    assert list(features.glob("*.md")) == []


def test_audit_and_compaction_documents_agent_context_budget_epic():
    """acb0 schema — epic + threshold Signature in governance handbook."""
    repo_root = Path(__file__).resolve().parents[1]
    text = (repo_root / "docs" / "governance" / "audit-and-compaction.md").read_text(
        encoding="utf-8",
    )
    assert "AgentContextBudget" in text
    assert "governance-compaction-drift-alert" in text
    assert "governance-always-on-rule-diet" in text
    assert "governance-index-not-grep" in text
    assert "governance-duplication-automation" in text
    assert "--duplication-threshold" in text


def test_compute_duplication_aggregates_sums_classify_and_kanban():
    dup = {
        "Classify quickly": 9,
        "triage §1 Classify": 51,
        "reference Classify signals": 49,
        "kanban-markdown SKILL (lifecycle)": 100,
        "kanban-markdown reference": 200,
    }
    agg = compute_duplication_aggregates(dup)
    assert agg[CLASSIFY_TRIO_SUM_LABEL] == 109
    assert agg[KANBAN_LIFECYCLE_SUM_LABEL] == 300


def test_compare_duplication_count_to_threshold_absolute_cap():
    assert (
        compare_duplication_count_to_threshold(
            750,
            700,
            warn_pct=20,
            critical_pct=50,
            warn_absolute=700,
            critical_absolute=1000,
        )
        == SEVERITY_WARN
    )
    assert (
        compare_duplication_count_to_threshold(
            1100,
            700,
            warn_pct=20,
            critical_pct=50,
            warn_absolute=700,
            critical_absolute=1000,
        )
        == SEVERITY_CRITICAL
    )


def test_duplication_threshold_fails_when_kanban_lifecycle_over_cap(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_baseline(repo)
    _minimal_gc0_repo(repo)
    ref = repo / ".cursor" / "skills" / "kanban-markdown" / "reference.md"
    ref.write_text("line\n" * 750, encoding="utf-8")
    skill = repo / ".cursor" / "skills" / "kanban-markdown" / "SKILL.md"
    skill.write_text("skill\n" * 200, encoding="utf-8")
    severity, signals = evaluate_duplication_thresholds(repo)
    labels = {sig.label for sig in signals}
    assert severity in {SEVERITY_WARN, SEVERITY_CRITICAL}
    assert KANBAN_LIFECYCLE_SUM_LABEL in labels


def test_duplication_threshold_lines_emits_prefix(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_baseline(repo)
    _minimal_gc0_repo(repo)
    ref = repo / ".cursor" / "skills" / "kanban-markdown" / "reference.md"
    ref.write_text("line\n" * 750, encoding="utf-8")
    lines = duplication_threshold_lines(repo, include_severity=True)
    assert len(lines) == 1
    assert PREFIX_DUPLICATION in lines[0]
    assert "governance-duplication-automation" in lines[0]


def test_main_duplication_threshold_exits_one(tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_baseline(repo)
    _minimal_gc0_repo(repo)
    ref = repo / ".cursor" / "skills" / "kanban-markdown" / "reference.md"
    ref.write_text("line\n" * 750, encoding="utf-8")
    features = repo / ".devtool" / "features"
    features.mkdir(parents=True)
    from scripts import check_governance_parity as mod

    code = mod.main(
        ["--repo-root", str(repo), "--duplication-threshold", "--no-spawn-cards"],
    )
    captured = capsys.readouterr()
    assert code == 1
    assert PREFIX_DUPLICATION in captured.out


def test_duplication_threshold_spawns_agent_card(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_baseline(repo)
    _minimal_gc0_repo(repo)
    ref = repo / ".cursor" / "skills" / "kanban-markdown" / "reference.md"
    ref.write_text("line\n" * 750, encoding="utf-8")
    features = repo / ".devtool" / "features"
    features.mkdir(parents=True)
    run_duplication_threshold_audit(
        repo_root=repo,
        features_dir=features,
        quiet=True,
        spawn_cards=True,
    )
    cards = list(features.glob("agent-governance-duplication-threshold-*.md"))
    assert len(cards) == 1
    body = cards[0].read_text(encoding="utf-8")
    assert 'labels: ["agent"]' in body
    assert "AgentContextBudget" in body
