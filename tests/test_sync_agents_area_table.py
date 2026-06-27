"""Tests for AGENTS.md area table sync from feature-areas.yaml (gs4)."""

from __future__ import annotations

from pathlib import Path

from scripts.check_governance_parity import PREFIX_REGISTRY, load_area_schema_entries
from scripts.sync_agents_area_table import (
    check_agents_area_table_parity,
    parse_agents_area_table,
    sync_agents_area_table_text,
)

_AREA_HEADING = "## Area → skills & rules (load when touching)\n\nIntro.\n\n"
_TABLE_HEADER = "| Area | Skill | Rule(s) |\n| ---- | ----- | ------- |\n"
_TABLE_SUFFIX = "\nPath→test map: hook\n\n## Next\n"

_SYNCED_ROW = (
    "| Agent / routing / self-eval | "
    "[agent-triage](.cursor/skills/agent-triage/SKILL.md), "
    "[agent-self-evaluation](.cursor/skills/agent-self-evaluation/SKILL.md), "
    "[kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md), "
    "[pre-commit-workflow](.cursor/skills/pre-commit-workflow/SKILL.md) | "
    "[agent-routing](.cursor/rules/agent-routing.mdc), "
    "[agent-self-evaluation](.cursor/rules/agent-self-evaluation.mdc), "
    "[agent-agents-md-maintenance](.cursor/rules/agent-agents-md-maintenance.mdc), "
    "[agent-consistency](.cursor/rules/agent-consistency.mdc), "
    "[kanban-card-gates](.cursor/rules/kanban-card-gates.mdc), "
    "[kanban-feature-cards](.cursor/rules/kanban-feature-cards.mdc), "
    "[kanban-bug-cards](.cursor/rules/kanban-bug-cards.mdc), "
    "[kanban-review-qa](.cursor/rules/kanban-review-qa.mdc), "
    "[kanban-commit-issue-cards](.cursor/rules/kanban-commit-issue-cards.mdc), "
    "[kanban-inquiry-cards](.cursor/rules/kanban-inquiry-cards.mdc), "
    "[kanban-agent-cards](.cursor/rules/kanban-agent-cards.mdc), "
    "[kanban-prior-lessons-gate](.cursor/rules/kanban-prior-lessons-gate.mdc), "
    "[testing](.cursor/rules/testing.mdc) |\n"
)

_MINIMAL_YAML = """
areas:
  Agent Workflow:
    paths:
      - AGENTS.md
      - .cursor/skills/agent-triage/
      - .cursor/skills/agent-self-evaluation/
      - .cursor/skills/kanban-markdown/
      - .cursor/skills/pre-commit-workflow/
    agents_skill: agent-triage
    agents_rules:
      - agent-routing.mdc
      - agent-self-evaluation.mdc
      - agent-agents-md-maintenance.mdc
      - agent-consistency.mdc
      - kanban-card-gates.mdc
      - kanban-feature-cards.mdc
      - kanban-bug-cards.mdc
      - kanban-review-qa.mdc
      - kanban-commit-issue-cards.mdc
      - kanban-inquiry-cards.mdc
      - kanban-agent-cards.mdc
      - kanban-prior-lessons-gate.mdc
      - testing.mdc
    lesson_routing_row: Agent Workflow
  Render Preview:
    paths:
      - ui/widgets/orbit_preview_widget.py
    agents_skill: ui-change
    agents_rules:
      - ui-panels.mdc
      - ui-general.mdc
    lesson_routing_row: Render Preview
"""


def _agents_with_rows(*rows: str) -> str:
    return _AREA_HEADING + _TABLE_HEADER + "".join(rows) + _TABLE_SUFFIX


def test_parse_agents_area_table_extracts_rows():
    text = _agents_with_rows(_SYNCED_ROW)
    table = parse_agents_area_table(text)
    assert table is not None
    assert len(table.rows) == 1
    assert "Agent / routing" in table.rows[0].area_label


def test_check_agents_area_table_parity_passes_when_yaml_matches():
    render_row = (
        "| Render Preview | [ui-change](.cursor/skills/ui-change/SKILL.md) | "
        "[ui-panels](.cursor/rules/ui-panels.mdc), "
        "[ui-general](.cursor/rules/ui-general.mdc) |\n"
    )
    text = _agents_with_rows(_SYNCED_ROW, render_row)
    entries = load_area_schema_entries(_MINIMAL_YAML)
    assert check_agents_area_table_parity(text, entries, _MINIMAL_YAML) == []


def test_check_agents_area_table_parity_detects_stale_skill():
    stale = (
        "| Agent / routing / self-eval | "
        "[agent-triage](.cursor/skills/agent-triage/SKILL.md) | "
        "[agent-routing](.cursor/rules/agent-routing.mdc) |\n"
    )
    render_row = (
        "| Render Preview | [ui-change](.cursor/skills/ui-change/SKILL.md) | "
        "[ui-panels](.cursor/rules/ui-panels.mdc), "
        "[ui-general](.cursor/rules/ui-general.mdc) |\n"
    )
    text = _agents_with_rows(stale, render_row)
    entries = load_area_schema_entries(_MINIMAL_YAML)
    issues = check_agents_area_table_parity(text, entries, _MINIMAL_YAML)
    assert any(
        PREFIX_REGISTRY in line and ("stale skills" in line or "missing skills" in line)
        for line in issues
    )


def test_check_agents_area_table_parity_detects_missing_yaml_row():
    text = _agents_with_rows(_SYNCED_ROW)
    entries = load_area_schema_entries(_MINIMAL_YAML)
    issues = check_agents_area_table_parity(text, entries, _MINIMAL_YAML)
    assert any(PREFIX_REGISTRY in line and "Render Preview" in line for line in issues)


def test_sync_agents_area_table_preserves_narrative_label():
    stale = (
        "| Agent / routing / self-eval | "
        "[agent-triage](.cursor/skills/agent-triage/SKILL.md) | "
        "[agent-routing](.cursor/rules/agent-routing.mdc) |\n"
    )
    render_row = (
        "| Render Preview | [ui-change](.cursor/skills/ui-change/SKILL.md) | "
        "[ui-panels](.cursor/rules/ui-panels.mdc), "
        "[ui-general](.cursor/rules/ui-general.mdc) |\n"
    )
    text = _agents_with_rows(stale, render_row)
    entries = load_area_schema_entries(_MINIMAL_YAML)
    synced = sync_agents_area_table_text(text, entries, _MINIMAL_YAML)
    assert "Agent / routing / self-eval" in synced
    assert "[kanban-markdown]" in synced
    assert check_agents_area_table_parity(synced, entries, _MINIMAL_YAML) == []


def test_sync_agents_area_table_on_repo_is_current():
    repo = Path(__file__).resolve().parent.parent
    agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
    yaml_text = (repo / "docs/feature-areas.yaml").read_text(encoding="utf-8")
    entries = load_area_schema_entries(yaml_text)
    assert check_agents_area_table_parity(agents, entries, yaml_text) == []
