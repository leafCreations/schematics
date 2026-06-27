"""Tests for governance parity checker."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_governance_parity import (
    EPIC_GOVERNANCE_DRIFT,
    EPIC_LESSONS_COVERAGE,
    PREFIX_CARD,
    PREFIX_FAILURE,
    PREFIX_LESSONS,
    PREFIX_REGISTRY,
    PREFIX_ROUTING,
    SEVERITY_CRITICAL,
    SEVERITY_WARN,
    AreaSchemaEntry,
    apply_severity,
    build_drift_card_body,
    check_area_schema_parity,
    check_card_type_parity,
    check_classify_parity,
    check_failure_pattern_parity,
    check_handlers_registry_parity,
    check_kanban_label_methods_handlers,
    check_kanban_rule_globs,
    check_lessons_coverage_drift,
    check_registry_parity,
    collect_always_apply_rules,
    collect_baseline_artifact_paths,
    collect_duplication_pair_counts,
    consolidate_drift_issues_for_spawn,
    create_drift_alert_cards,
    default_severity_for_line,
    extract_agents_governance_paths,
    extract_label_method_symbols,
    extract_lessons_by_area_first_column,
    filter_registry_compare_paths,
    format_drift_line,
    format_line_count_report,
    is_schema_internal_registry_path,
    is_valid_handler_symbol,
    issue_card_id,
    load_agent_workflow_paths,
    load_area_handlers,
    load_area_schema_entries,
    parse_drift_line,
    priority_for_severity,
    run_checks,
    section_line_count,
)

AGENTS_CLASSIFY_SNIPPET = """
## Classify quickly

| Signal | Mode | First read |
| ------ | ---- | ---------- |
| Review kanban card only (`review …`, bare `@path`) | **Ask-only** | Card |
| Update / spawn / implement card (agent verbs) | **Agent** | Card |
| Card missing / empty / unknown `labels` | **Block** | Stop |
| Implement / fix without a card | **Ask-only** | kanban card |
| All other signals | *see reference* | reference § Classify |
"""

TRIAGE_CLASSIFY_SNIPPET = """
## 1. Classify the request

**Canonical table:** reference.md § Classify — Signature: governance-compact-classify-ssot.
"""

REFERENCE_CLASSIFY_SNIPPET = """
## Classify the request (signals)

| Signal | Mode | First action (short) |
| ------ | ---- | -------------------- |
| **Review** kanban card only (`review …`, bare `@path`) | Ask-only | kanban-card-gates §2 |
| **Update / spawn / implement** card (agent verbs) | Agent | kanban-markdown |
| `Kanban: answer inquiry on …` | Agent | Inquiry **Response** |
| Card missing / empty / unknown `labels` | Block | Stop |
| Implement / fix without a card | Ask-only | kanban card required |
| Review QA on assigned card | Review | kanban-review-qa |
| User says feature / bug / agent / commit-issue Done | Governance | Card Done |
| User says inquiry Done | Close only | No lessons |
| AGENTS.md governance audit | Read-only | Periodic audit |
| Lessons coverage drift / low composite | Governance | check_lessons_coverage |
| Explain / audit / is this correct? | Ask-only | Grep + read |
| Pre-commit failed | Unblock / Review | §1b pre-commit |
| Failing test / pytest / ruff (no card) | Ask-only / Unblock | §1b failure routing |
| UI wiring / dialog (no card) | Ask-only | ui-dialog-no-persist |
| Orbit 3D holes (no card) | Ask-only | orbit-stair-mask-transparency |
| Agent handoff / process mistake | Governance | self-eval reference |
| Agent `.tmp-venv` / missing venv | Ask-only / Unblock | agent-no-tmp-venv |
| Repeated mistake / churn | Grep | §1b failure routing |
| Run tests / commit-ready | Verify | targeted-testing |
| Area lesson lookup (kanban + Feature Areas) | Review first | lessons-index.yaml |
"""

_AGENTS_AREA_ROW = (
    "| Agent / routing / self-eval | "
    "[agent-triage](.cursor/skills/agent-triage/SKILL.md) | "
    "[agent-routing](.cursor/rules/agent-routing.mdc) |\n"
)
AGENTS_AREA_SNIPPET = f"""
## Area → skills & rules

| Area | Skill | Rule(s) |
| ---- | ----- | ------- |
{_AGENTS_AREA_ROW}"""

AGENTS_CARD_TYPES = """
### Card types (`labels` in frontmatter)

| Label | User provides | Agent provides |
| ----- | ------------- | -------------- |
| `feature` | Feature Areas | Decisions |
| `bug` | Steps | Root Cause |
| `inquiry` | Description | Response |
| `agent` | Description | Decisions |
| `commit-issue` | Problem | Corrective Action |
"""


def test_check_classify_parity_passes_when_canonical_ssot(monkeypatch: pytest.MonkeyPatch):
    from scripts import check_governance_parity as mod

    fp = mod._classify_signal_fingerprint(
        mod._table_first_column(mod._classify_signals_section(REFERENCE_CLASSIFY_SNIPPET))
    )
    monkeypatch.setattr(mod, "REFERENCE_CLASSIFY_FINGERPRINT", fp)
    assert (
        check_classify_parity(
            AGENTS_CLASSIFY_SNIPPET,
            TRIAGE_CLASSIFY_SNIPPET,
            REFERENCE_CLASSIFY_SNIPPET,
        )
        == []
    )


def test_check_classify_parity_passes_on_repo_artifacts():
    repo = Path(__file__).resolve().parent.parent
    agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
    triage = (repo / ".cursor/skills/agent-triage/SKILL.md").read_text(encoding="utf-8")
    ref = (repo / ".cursor/skills/agent-triage/reference.md").read_text(encoding="utf-8")
    assert check_classify_parity(agents, triage, ref) == []


def test_check_classify_parity_detects_missing_reference_anchor():
    issues = check_classify_parity(
        AGENTS_CLASSIFY_SNIPPET,
        TRIAGE_CLASSIFY_SNIPPET,
        "## Classify the request (signals)\n\n| Signal | Mode |\n| --- | --- |\n",
    )
    assert any(PREFIX_ROUTING in line and "review card" in line.lower() for line in issues)


def test_check_classify_parity_detects_agents_too_many_rows():
    bloated = AGENTS_CLASSIFY_SNIPPET + "\n| extra one | x | y |\n| extra two | x | y |\n"
    issues = check_classify_parity(
        bloated,
        TRIAGE_CLASSIFY_SNIPPET,
        REFERENCE_CLASSIFY_SNIPPET,
    )
    assert any(PREFIX_ROUTING in line and "max 5" in line for line in issues)


def test_check_classify_parity_detects_triage_duplicate_table():
    triage_with_table = """
## 1. Classify the request

| Signal | Mode |
| ------ | ---- |
| Review card | Ask-only |
"""
    issues = check_classify_parity(
        AGENTS_CLASSIFY_SNIPPET,
        triage_with_table,
        REFERENCE_CLASSIFY_SNIPPET,
    )
    assert any(PREFIX_ROUTING in line and "triage §1" in line for line in issues)


def test_check_classify_parity_detects_reference_fingerprint_drift():
    short_ref = REFERENCE_CLASSIFY_SNIPPET.replace(
        "Area lesson lookup (kanban + Feature Areas)",
        "Area lesson lookup changed",
    )
    issues = check_classify_parity(
        AGENTS_CLASSIFY_SNIPPET,
        TRIAGE_CLASSIFY_SNIPPET,
        short_ref,
    )
    assert any(PREFIX_ROUTING in line and "fingerprint drift" in line for line in issues)


def test_check_failure_pattern_parity_detects_missing_reference_row():
    issues = check_failure_pattern_parity(
        {"known-sig"},
        {"known-sig", "orphan-sig"},
    )
    assert len(issues) == 1
    assert PREFIX_FAILURE in issues[0]
    assert "orphan-sig" in issues[0]


def test_check_failure_pattern_parity_passes_when_cites_known():
    assert check_failure_pattern_parity({"known-sig"}, {"known-sig"}) == []


def test_check_registry_parity_detects_yaml_only_path():
    issues = check_registry_parity(
        {".cursor/skills/agent-triage/", "AGENTS.md"},
        {"AGENTS.md"},
    )
    assert any(PREFIX_REGISTRY in line and "agent-triage" in line for line in issues)


def test_check_registry_parity_detects_agents_only_path():
    issues = check_registry_parity(
        {"AGENTS.md"},
        {"AGENTS.md", ".cursor/skills/agent-triage/"},
    )
    assert any(PREFIX_REGISTRY in line and "agent-triage" in line for line in issues)


def test_check_registry_parity_ignores_mdc_rule_paths():
    """Rule links are checked by area table sync — not registry path parity."""
    assert (
        check_registry_parity(
            {"AGENTS.md"},
            {"AGENTS.md", ".cursor/rules/agent-routing.mdc"},
        )
        == []
    )


def test_is_schema_internal_registry_path():
    assert is_schema_internal_registry_path("docs/lessons-index.yaml")
    assert is_schema_internal_registry_path("scripts/resolve_prior_lessons.py")
    assert is_schema_internal_registry_path("scripts/resolve_feature_areas.py")
    assert is_schema_internal_registry_path("scripts/check_lessons_coverage.py")
    assert is_schema_internal_registry_path("scripts/lessons_coverage_lib.py")
    assert is_schema_internal_registry_path("scripts/pre-commit-lessons-coverage.sh")
    assert is_schema_internal_registry_path("tests/test_check_lessons_coverage.py")
    assert not is_schema_internal_registry_path(".cursor/skills/agent-triage/")


def test_filter_registry_compare_paths_drops_schema_internal():
    paths = {
        "AGENTS.md",
        "docs/lessons-index.yaml",
        "scripts/resolve_prior_lessons.py",
    }
    assert filter_registry_compare_paths(paths) == {"AGENTS.md"}


def test_check_registry_parity_ignores_schema_internal_yaml_only():
    issues = check_registry_parity(
        {
            "AGENTS.md",
            "docs/lessons-index.yaml",
            "scripts/resolve_prior_lessons.py",
        },
        {"AGENTS.md"},
    )
    assert issues == []


def test_check_registry_parity_ignores_lessons_coverage_paths():
    """Lessons Coverage Metric tooling is schema-internal — not AGENTS area row links."""
    yaml_paths = {
        "AGENTS.md",
        "scripts/check_lessons_coverage.py",
        "scripts/lessons_coverage_lib.py",
        "scripts/pre-commit-lessons-coverage.sh",
        "tests/test_check_lessons_coverage.py",
    }
    assert check_registry_parity(yaml_paths, {"AGENTS.md"}) == []


def test_load_area_schema_entries_skips_areas_without_agents_skill():
    yaml_text = """
areas:
  Plain Area:
    paths:
      - ui/foo.py
  Seeded Area:
    agents_skill: agent-triage
    agents_rules:
      - agent-routing.mdc
    lesson_routing_row: Agent Workflow
    lesson_signatures:
      - lessons-by-area-routing
"""
    entries = load_area_schema_entries(yaml_text)
    assert len(entries) == 1
    assert entries[0].name == "Seeded Area"
    assert entries[0].agents_skill == "agent-triage"


def test_check_area_schema_parity_detects_missing_skill(tmp_path: Path):
    issues = check_area_schema_parity(
        tmp_path,
        [
            AreaSchemaEntry(
                name="Bad Area",
                agents_skill="missing-skill",
                agents_rules=(),
                lesson_routing_row=None,
                lesson_signatures=(),
            )
        ],
        "## Lessons by area\n\n| Signal | Read |\n| --- | --- |\n",
        "areas: {}\n",
        set(),
    )
    assert len(issues) == 1
    assert PREFIX_REGISTRY in issues[0]
    assert "missing-skill" in issues[0]


def test_check_area_schema_parity_detects_missing_lesson_routing_row(tmp_path: Path):
    (tmp_path / ".cursor/skills/ui-change").mkdir(parents=True)
    (tmp_path / ".cursor/skills/ui-change/SKILL.md").write_text("# skill\n", encoding="utf-8")
    issues = check_area_schema_parity(
        tmp_path,
        [
            AreaSchemaEntry(
                name="Render Preview",
                agents_skill="ui-change",
                agents_rules=(),
                lesson_routing_row="Not In Table",
                lesson_signatures=(),
            )
        ],
        "## Lessons by area\n\n| Signal | Read |\n| --- | --- |\n| **Render Preview** | docs |\n",
        "areas: {}\n",
        set(),
    )
    assert len(issues) == 1
    assert "lesson_routing_row" in issues[0]
    assert "Not In Table" in issues[0]


def test_extract_lessons_by_area_first_column():
    reference = """## Lessons by area (read before card grep)

| Signal / Feature Area | Read first |
| --------------------- | ---------- |
| **Render Preview** — orbit | docs |
| **Agent Workflow** — routing | index |
"""
    rows = extract_lessons_by_area_first_column(reference)
    assert any("render preview" in row.lower() for row in rows)
    assert any("agent workflow" in row.lower() for row in rows)


def test_load_agent_workflow_paths_from_yaml():
    yaml_text = """
areas:
  Agent Workflow:
    paths:
      - AGENTS.md
      - .cursor/skills/agent-triage/
"""
    assert load_agent_workflow_paths(yaml_text) == {
        "AGENTS.md",
        ".cursor/skills/agent-triage/",
    }


def test_load_area_handlers_from_yaml():
    yaml_text = """
areas:
  Preview Toolbar:
    handlers:
      - PreviewToolbar.zoom_changed
      - PreviewToolbar.set_zoom_percent
  File Menu:
    handlers:
      - MainWindow._init_file_menu
"""
    assert load_area_handlers(yaml_text) == {
        "Preview Toolbar": [
            "PreviewToolbar.zoom_changed",
            "PreviewToolbar.set_zoom_percent",
        ],
        "File Menu": ["MainWindow._init_file_menu"],
    }


def test_is_valid_handler_symbol():
    assert is_valid_handler_symbol("MainWindow._on_open_structure")
    assert is_valid_handler_symbol("load_editor_settings")
    assert is_valid_handler_symbol("test_pick_structure_stage_*")
    assert not is_valid_handler_symbol("ui/main_window.py")
    assert not is_valid_handler_symbol("")
    assert not is_valid_handler_symbol("bad handler")


def test_check_handlers_registry_parity_passes_clean_handlers():
    handlers = {
        "Preview Toolbar": ["PreviewToolbar.zoom_changed"],
        "File Menu": ["MainWindow._init_file_menu"],
    }
    assert check_handlers_registry_parity(handlers) == []


def test_check_handlers_registry_parity_detects_duplicate():
    handlers = {
        "Area A": ["MainWindow._shared"],
        "Area B": ["MainWindow._shared"],
    }
    issues = check_handlers_registry_parity(handlers)
    assert len(issues) == 1
    assert PREFIX_REGISTRY in issues[0]
    assert "MainWindow._shared" in issues[0]


def test_check_handlers_registry_parity_detects_malformed():
    issues = check_handlers_registry_parity(
        {"Broken Area": ["ui/widgets/preview_panel.py"]},
    )
    assert len(issues) == 1
    assert PREFIX_REGISTRY in issues[0]
    assert "malformed" in issues[0]


def test_extract_label_method_symbols_from_card_body():
    card = """
## Feature Areas

`Preview Toolbar`

## Label Methods

- `ui/widgets/preview_toolbar.py` — `PreviewToolbar.zoom_changed`
- `PreviewPanel.restore_saved_zoom`
"""
    symbols = extract_label_method_symbols(card)
    assert symbols == {"PreviewToolbar.zoom_changed", "PreviewPanel.restore_saved_zoom"}


def test_check_kanban_label_methods_handlers_detects_missing_symbol(tmp_path: Path):
    features = tmp_path / "features"
    features.mkdir()
    (features / "todo-card.md").write_text(
        """---
status: "todo"
order: "a0"
---
# Example

## Feature Areas

`Preview Toolbar`

## Label Methods

- `PreviewToolbar.not_in_registry`
""",
        encoding="utf-8",
    )
    handlers = {"Preview Toolbar": ["PreviewToolbar.zoom_changed"]}
    issues = check_kanban_label_methods_handlers(features, handlers)
    assert len(issues) == 1
    assert PREFIX_REGISTRY in issues[0]
    assert "not_in_registry" in issues[0]


def test_check_kanban_label_methods_handlers_passes_registered_symbol(tmp_path: Path):
    features = tmp_path / "features"
    features.mkdir()
    (features / "todo-card.md").write_text(
        """---
status: "todo"
order: "a0"
---
# Example

## Feature Areas

`Preview Toolbar`

## Label Methods

- `PreviewToolbar.zoom_changed`
""",
        encoding="utf-8",
    )
    handlers = {"Preview Toolbar": ["PreviewToolbar.zoom_changed"]}
    assert check_kanban_label_methods_handlers(features, handlers) == []


def test_extract_agents_governance_paths_from_area_table():
    paths = extract_agents_governance_paths(AGENTS_AREA_SNIPPET)
    assert ".cursor/skills/agent-triage/" in paths
    assert ".cursor/rules/agent-routing.mdc" in paths
    assert "AGENTS.md" in paths


def test_check_card_type_parity_detects_unknown_label():
    issues = check_card_type_parity(
        {"refactor"},
        {"bug", "inquiry"},
    )
    assert any(PREFIX_CARD in line and "refactor" in line for line in issues)


def test_check_card_type_parity_passes_for_known_labels():
    known = {"feature", "bug", "inquiry", "commit-issue", "agent"}
    assert check_card_type_parity({"bug"}, known) == []


def test_check_kanban_rule_globs_passes_on_repo():
    repo_root = Path(__file__).resolve().parents[1]
    assert check_kanban_rule_globs(repo_root) == []


def test_check_kanban_rule_globs_detects_always_apply_on_card_type(tmp_path: Path):
    rules = tmp_path / ".cursor" / "rules"
    rules.mkdir(parents=True)
    (rules / "kanban-card-gates.mdc").write_text(
        "---\nalwaysApply: true\n---\n",
        encoding="utf-8",
    )
    (rules / "kanban-bug-cards.mdc").write_text(
        "---\nalwaysApply: true\n---\n",
        encoding="utf-8",
    )
    for name in (
        "kanban-feature-cards.mdc",
        "kanban-agent-cards.mdc",
        "kanban-inquiry-cards.mdc",
        "kanban-commit-issue-cards.mdc",
    ):
        (rules / name).write_text(
            "---\nglobs: .devtool/features/**/*.md\nalwaysApply: false\n---\n",
            encoding="utf-8",
        )
    issues = check_kanban_rule_globs(tmp_path)
    assert any("kanban-bug-cards.mdc" in line and "alwaysApply" in line for line in issues)


def test_run_checks_integration_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from scripts import check_governance_parity as mod

    fp = mod._classify_signal_fingerprint(
        mod._table_first_column(mod._classify_signals_section(REFERENCE_CLASSIFY_SNIPPET))
    )
    monkeypatch.setattr(mod, "REFERENCE_CLASSIFY_FINGERPRINT", fp)

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text(
        AGENTS_CLASSIFY_SNIPPET + AGENTS_CARD_TYPES + AGENTS_AREA_SNIPPET,
        encoding="utf-8",
    )
    triage_dir = repo / ".cursor/skills/agent-triage"
    triage_dir.mkdir(parents=True)
    (triage_dir / "SKILL.md").write_text(TRIAGE_CLASSIFY_SNIPPET, encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs/feature-areas.yaml").write_text(
        """
areas:
  Agent Workflow:
    paths:
      - AGENTS.md
      - .cursor/skills/agent-triage/
      - .cursor/rules/agent-routing.mdc
    agents_skill: agent-triage
    agents_rules:
      - agent-routing.mdc
    lesson_routing_row: Agent Workflow
""",
        encoding="utf-8",
    )
    features = repo / ".devtool/features"
    features.mkdir(parents=True)
    (features / "bug-card.md").write_text(
        '---\nlabels: ["bug"]\n---\n',
        encoding="utf-8",
    )
    rules_dir = repo / ".cursor/rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "agent-routing.mdc").write_text("routing\n", encoding="utf-8")
    (rules_dir / mod.KANBAN_ALWAYS_ON_RULE).write_text(
        "---\nalwaysApply: true\n---\n",
        encoding="utf-8",
    )
    for name in mod.KANBAN_CARD_TYPE_RULE_NAMES:
        (rules_dir / name).write_text(
            "---\nglobs: .devtool/features/**/*.md\nalwaysApply: false\n---\n",
            encoding="utf-8",
        )

    ref_dir = repo / ".cursor/skills/agent-self-evaluation"
    ref_dir.mkdir(parents=True)
    (ref_dir / "reference.md").write_text(
        "| `known-sig` | trigger | fix | skill | — |\n",
        encoding="utf-8",
    )
    pre_dir = repo / ".cursor/skills/pre-commit-workflow"
    pre_dir.mkdir(parents=True)
    (pre_dir / "reference.md").write_text("", encoding="utf-8")
    (triage_dir / "reference.md").write_text(
        REFERENCE_CLASSIFY_SNIPPET
        + "\n## Lessons by area\n\n| Signal | Read |\n| --- | --- |\n"
        + "| **Agent Workflow** | read |\n",
        encoding="utf-8",
    )
    (repo / "docs/lessons-index.yaml").write_text("areas: {}\n", encoding="utf-8")

    issues = run_checks(
        repo_root=repo,
        agents_text=(repo / "AGENTS.md").read_text(encoding="utf-8"),
        triage_text=(triage_dir / "SKILL.md").read_text(encoding="utf-8"),
        feature_areas_text=(repo / "docs/feature-areas.yaml").read_text(encoding="utf-8"),
        features_dir=features,
        rule_paths=[rules_dir / "agent-routing.mdc"],
        reference_paths=(
            ref_dir / "reference.md",
            pre_dir / "reference.md",
        ),
        triage_reference_text=(triage_dir / "reference.md").read_text(encoding="utf-8"),
        lessons_index_text=(repo / "docs/lessons-index.yaml").read_text(encoding="utf-8"),
        include_severity=False,
    )
    assert issues == []


def test_main_exit_code_nonzero_on_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text(AGENTS_CLASSIFY_SNIPPET, encoding="utf-8")
    triage_dir = repo / ".cursor/skills/agent-triage"
    triage_dir.mkdir(parents=True)
    (triage_dir / "SKILL.md").write_text(
        "## 1. Classify\n\n| Signal | Mode |\n| --- | --- |\n",
        encoding="utf-8",
    )
    (repo / "docs").mkdir()
    (repo / "docs/feature-areas.yaml").write_text(
        "areas:\n  Agent Workflow:\n    paths:\n      - AGENTS.md\n",
        encoding="utf-8",
    )
    triage_ref = triage_dir / "reference.md"
    triage_ref.write_text(
        "## Lessons by area\n\n| Signal | Read |\n| --- | --- |\n",
        encoding="utf-8",
    )
    (repo / "docs/lessons-index.yaml").write_text("areas: {}\n", encoding="utf-8")
    (repo / ".devtool/features").mkdir(parents=True)

    from scripts import check_governance_parity as mod

    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    assert mod.main(["--repo-root", str(repo), "--plain", "--no-spawn-cards"]) == 1


def test_default_severity_for_line():
    routing = f"{PREFIX_ROUTING} example"
    failure = f"{PREFIX_FAILURE} example"
    assert default_severity_for_line(routing) == SEVERITY_WARN
    assert default_severity_for_line(failure) == SEVERITY_CRITICAL


def test_format_drift_line_adds_severity_prefix():
    line = f"{PREFIX_ROUTING} AGENTS Classify row missing"
    assert format_drift_line(line) == f"[{SEVERITY_WARN}] {line}"


def test_apply_severity_on_failure_pattern():
    raw = [f"{PREFIX_FAILURE} Rule cites `orphan` — no reference row"]
    formatted = apply_severity(raw, include_severity=True)
    assert formatted[0].startswith(f"[{SEVERITY_CRITICAL}]")


def test_priority_for_severity():
    assert priority_for_severity("info") == "low"
    assert priority_for_severity("warn") == "medium"
    assert priority_for_severity("critical") == "high"


def test_parse_drift_line_strips_severity_prefix():
    raw = f"{PREFIX_ROUTING} AGENTS row missing"
    line = format_drift_line(raw)
    issue = parse_drift_line(line)
    assert issue.severity == SEVERITY_WARN
    assert issue.message == raw


def test_build_drift_card_body_sections():
    issue = parse_drift_line(format_drift_line(f"{PREFIX_REGISTRY} yaml path missing in AGENTS"))
    body = build_drift_card_body(issue)
    assert "## Alert" in body
    assert "## Feature Areas" in body
    assert "`Feature Area Registry`" in body
    assert "## Label Paths" in body
    assert "## Label Methods" in body
    assert "## Decisions" in body
    assert "## Acceptance Criteria" in body
    assert "## Corrective Action" not in body
    assert issue.message in body


def test_build_drift_card_body_agent_spawn_sections():
    issue = parse_drift_line(format_drift_line(f"{PREFIX_LESSONS} composite 50.0% (threshold 75%)"))
    body = build_drift_card_body(issue)
    assert "## Description" in body
    assert "## Feature Area" in body
    assert "## Label Methods" in body
    assert "## Decisions" in body
    assert "## Acceptance Criteria" in body
    assert "## Feature Areas" not in body
    assert "## Corrective Action" not in body


def test_create_drift_alert_cards_writes_todo_card(tmp_path: Path):
    features = tmp_path / "features"
    line = format_drift_line(f"{PREFIX_ROUTING} AGENTS Classify row missing in triage §1")
    paths = create_drift_alert_cards([line], features_dir=features)
    assert len(paths) == 1
    text = paths[0].read_text(encoding="utf-8")
    assert f'epic: "{EPIC_GOVERNANCE_DRIFT}"' in text
    assert 'status: "todo"' in text
    assert 'priority: "medium"' in text
    assert "## Alert" in text
    assert "## Label Methods" in text
    assert "## Decisions" in text
    assert "## Acceptance Criteria" in text
    assert "## Corrective Action" not in text


def test_create_drift_alert_cards_critical_priority(tmp_path: Path):
    features = tmp_path / "features"
    line = format_drift_line(f"{PREFIX_FAILURE} Rule cites `orphan-sig` — no reference row")
    paths = create_drift_alert_cards([line], features_dir=features)
    assert 'priority: "high"' in paths[0].read_text(encoding="utf-8")


def test_create_drift_alert_cards_skips_duplicate_alert(tmp_path: Path):
    features = tmp_path / "features"
    line = format_drift_line(f"{PREFIX_ROUTING} duplicate alert example")
    first = create_drift_alert_cards([line], features_dir=features)
    second = create_drift_alert_cards([line], features_dir=features)
    assert len(first) == 1
    assert len(second) == 0


def test_consolidate_registry_label_methods_per_kanban_card():
    card = "feature-stair-2026-06-27.md"
    lines = [
        format_drift_line(
            f"{PREFIX_REGISTRY} kanban `{card}` Label Methods `compose_stairs` "
            "missing from feature-areas.yaml `handlers:`"
        ),
        format_drift_line(
            f"{PREFIX_REGISTRY} kanban `{card}` Label Methods `build_stair_top_mask` "
            "missing from feature-areas.yaml `handlers:`"
        ),
    ]
    merged = consolidate_drift_issues_for_spawn(lines)
    assert len(merged) == 1
    assert "`compose_stairs`" in merged[0]
    assert "`build_stair_top_mask`" in merged[0]
    assert f"kanban `{card}` — Label Methods symbols" in merged[0]


def test_create_drift_alert_cards_one_card_for_multiple_registry_symbols(tmp_path: Path):
    features = tmp_path / "features"
    card = "feature-stair-2026-06-27.md"
    lines = [
        format_drift_line(
            f"{PREFIX_REGISTRY} kanban `{card}` Label Methods `sym_a` "
            "missing from feature-areas.yaml `handlers:`"
        ),
        format_drift_line(
            f"{PREFIX_REGISTRY} kanban `{card}` Label Methods `sym_b` "
            "missing from feature-areas.yaml `handlers:`"
        ),
    ]
    paths = create_drift_alert_cards(lines, features_dir=features)
    assert len(paths) == 1
    text = paths[0].read_text(encoding="utf-8")
    assert "`sym_a`" in text
    assert "`sym_b`" in text


def test_issue_card_id_is_stable_for_same_message():
    issue = parse_drift_line(f"{PREFIX_ROUTING} stable message")
    assert issue_card_id(issue) == issue_card_id(issue)


def test_section_line_count_counts_non_empty_lines():
    text = "## Heading\n\n| a | b |\n| --- | --- |\n| x | y |\n\n## Next\n"
    assert section_line_count(text, "## Heading") == 3


def test_collect_baseline_artifact_paths_includes_agents_and_kanban_rules(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
    rules = repo / ".cursor/rules"
    rules.mkdir(parents=True)
    (rules / "kanban-bug-cards.mdc").write_text("bug\n", encoding="utf-8")
    (rules / "agent-routing.mdc").write_text("route\n", encoding="utf-8")
    rels = {rel for rel, _path in collect_baseline_artifact_paths(repo)}
    assert "AGENTS.md" in rels
    assert ".cursor/rules/kanban-bug-cards.mdc" in rels
    assert ".cursor/rules/agent-routing.mdc" in rels


def test_format_line_count_report_lists_artifacts_and_always_on(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text("line one\nline two\n", encoding="utf-8")
    rules = repo / ".cursor/rules"
    rules.mkdir(parents=True)
    (rules / "agent-routing.mdc").write_text(
        "---\nalwaysApply: true\n---\nroute\n",
        encoding="utf-8",
    )
    report = format_line_count_report(repo)
    assert "Governance compaction baseline" in report
    assert "AGENTS.md" in report
    assert "Always-on rules" in report
    assert "agent-routing.mdc" in report


def test_collect_duplication_pair_counts_classify_sections(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text(
        "## Classify quickly\n\n| Signal | Mode |\n| --- | --- |\n| row | x |\n",
        encoding="utf-8",
    )
    triage = repo / ".cursor/skills/agent-triage"
    triage.mkdir(parents=True)
    (triage / "SKILL.md").write_text(
        "## 1. Classify the request\n\n| Signal | Mode |\n| --- | --- |\n",
        encoding="utf-8",
    )
    (triage / "reference.md").write_text(
        "## Classify the request (signals)\n\n| a |\n",
        encoding="utf-8",
    )
    rows = {label: count for label, _path, count in collect_duplication_pair_counts(repo)}
    assert rows["Classify quickly"] >= 2
    assert rows["triage §1 Classify"] >= 2


def test_collect_always_apply_rules_tags_governance(tmp_path: Path):
    repo = tmp_path / "repo"
    rules = repo / ".cursor/rules"
    rules.mkdir(parents=True)
    (rules / "agent-routing.mdc").write_text("---\nalwaysApply: true\n---\n", encoding="utf-8")
    (rules / "worldgen.mdc").write_text("---\nalwaysApply: true\n---\n", encoding="utf-8")
    rows = collect_always_apply_rules(repo)
    by_path = {rel: (count, is_gov) for rel, count, is_gov in rows}
    assert by_path[".cursor/rules/agent-routing.mdc"][1] is True
    assert by_path[".cursor/rules/worldgen.mdc"][1] is False


def test_main_line_counts_exits_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
    from scripts import check_governance_parity as mod

    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    assert mod.main(["--repo-root", str(repo), "--line-counts"]) == 0
    captured = capsys.readouterr()
    assert "Governance compaction baseline" in captured.out


def _write_done_card(done_dir: Path, name: str, body: str, *, epic: str = "CovEpic") -> None:
    done_dir.mkdir(parents=True, exist_ok=True)
    (done_dir / name).write_text(f"---\nepic: {epic}\n---\n\n{body}", encoding="utf-8")


def test_check_lessons_coverage_drift_skips_without_done_dir(tmp_path: Path):
    features = tmp_path / "features"
    features.mkdir()
    assert check_lessons_coverage_drift(features, include_severity=False) == []


def test_check_lessons_coverage_drift_emits_breakdown(tmp_path: Path, monkeypatch):
    import scripts.lessons_coverage_lib as lib
    import scripts.resolve_prior_lessons as rpl

    features = tmp_path / "features"
    done = features / "done"
    monkeypatch.setattr(lib, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(rpl, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(rpl, "FEATURES_DIR", features)
    monkeypatch.setattr(rpl, "DONE_DIR", done)
    monkeypatch.setattr(rpl, "ARCHIVED_DIR", features / "archived")
    monkeypatch.setattr(lib, "_known_signatures", lambda: set())
    monkeypatch.setattr(lib, "_path_exists", lambda _path: False)

    _write_done_card(
        done,
        "lesson.md",
        "## Lessons captured (2026-06-27)\n\n- no promotion\n",
        epic="LowEpic",
    )
    active = features / "active.md"
    active.write_text(
        "---\nstatus: review\nepic: LowEpic\n---\n\n"
        "## Feature Area\n\n`Agent Workflow`\n\n"
        "## Label Paths\n\n- `scripts/foo.py`\n\n"
        "## Decisions\n\n- plan\n",
        encoding="utf-8",
    )

    issues = check_lessons_coverage_drift(features, include_severity=False)
    assert len(issues) == 1
    assert issues[0].startswith(PREFIX_LESSONS)
    assert "C1 Capture" in issues[0]
    assert "C4 Application" in issues[0]


def test_check_lessons_coverage_drift_critical_below_sixty(tmp_path: Path, monkeypatch):
    import scripts.lessons_coverage_lib as lib
    import scripts.resolve_prior_lessons as rpl

    features = tmp_path / "features"
    done = features / "done"
    monkeypatch.setattr(lib, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(rpl, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(rpl, "FEATURES_DIR", features)
    monkeypatch.setattr(rpl, "DONE_DIR", done)
    monkeypatch.setattr(rpl, "ARCHIVED_DIR", features / "archived")
    monkeypatch.setattr(lib, "_known_signatures", lambda: set())
    monkeypatch.setattr(lib, "_path_exists", lambda _path: False)

    _write_done_card(
        done,
        "lesson.md",
        "## Lessons captured (2026-06-27)\n\n- no promotion\n",
        epic="LowEpic",
    )
    active = features / "active.md"
    active.write_text(
        "---\nstatus: review\nepic: LowEpic\n---\n\n"
        "## Feature Area\n\n`Agent Workflow`\n\n"
        "## Label Paths\n\n- `scripts/foo.py`\n\n"
        "## Decisions\n\n- plan\n",
        encoding="utf-8",
    )

    issues = check_lessons_coverage_drift(features, include_severity=True)
    assert issues[0].startswith(f"[{SEVERITY_CRITICAL}]")


def test_create_lessons_coverage_drift_card_epic(tmp_path: Path):
    features = tmp_path / "features"
    features.mkdir()
    line = (
        f"{PREFIX_LESSONS} composite 50.0% (threshold 75%) — "
        "C1 Capture: 0.0% (0/1 — 0/1 cards with resolvable promotions)"
    )
    created = create_drift_alert_cards([line], features_dir=features)
    assert len(created) == 1
    text = created[0].read_text(encoding="utf-8")
    assert f'epic: "{EPIC_LESSONS_COVERAGE}"' in text
    assert 'labels: ["agent"]' in text
    assert "lessons-coverage-drift-" in text
    assert "## Description" in text
    assert "## Feature Area" in text
    assert "## Label Methods" in text
    assert "## Decisions" in text
    assert "## Acceptance Criteria" in text
