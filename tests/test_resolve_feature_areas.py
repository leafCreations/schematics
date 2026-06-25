"""Tests for feature area registry resolver."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from scripts.check_governance_parity import (
    AreaSchemaEntry,
    check_area_schema_parity,
    load_area_schema_entries,
)
from scripts.resolve_feature_areas import (
    AgentsParityInfo,
    format_agents_parity,
    format_lesson_pointers,
    lessons_by_area_row_found,
    load_registry,
    main,
    parse_agents_governance_keys,
    resolve_agents_parity,
    resolve_areas,
    resolve_lesson_pointers,
)


def test_resolve_areas_returns_paths():
    paths, unknown = resolve_areas(["File Menu"])
    assert not unknown
    assert "ui/main_window.py" in paths


def test_resolve_areas_handlers_only():
    handlers, unknown = resolve_areas(["Open Structures Workflow"], handlers_only=True)
    assert not unknown
    assert "MainWindow._on_open_structure" in handlers
    assert "ui/reload.py" not in handlers


def test_resolve_areas_unknown_label():
    paths, unknown = resolve_areas(["Not A Real Area"])
    assert paths == []
    assert unknown == ["Not A Real Area"]


def test_load_registry_includes_lesson_keys():
    areas = load_registry()
    render = areas["Render Preview"]
    assert "orbit-animated-texture-strip" in render["lesson_signatures"]
    assert "docs/render-types.md" in render["lesson_docs"]
    agent = areas["Agent Workflow"]
    assert "precommit-stash-old-hooks" in agent["lesson_signatures"]
    assert "docs/development.md" in agent["lesson_docs"]


def test_resolve_lesson_pointers_single_area():
    pointers, unknown = resolve_lesson_pointers(["Render Preview"])
    assert not unknown
    assert "orbit-animated-texture-strip" in pointers["lesson_signatures"]
    assert pointers["lesson_docs"] == ["docs/render-types.md"]


def test_resolve_lesson_pointers_unions_dual_labels():
    pointers, unknown = resolve_lesson_pointers(["Render Preview", "Agent Workflow"])
    assert not unknown
    assert "orbit-animated-texture-strip" in pointers["lesson_signatures"]
    assert "precommit-stash-old-hooks" in pointers["lesson_signatures"]
    assert "docs/render-types.md" in pointers["lesson_docs"]
    assert "docs/development.md" in pointers["lesson_docs"]


def test_resolve_lesson_pointers_unknown_label():
    pointers, unknown = resolve_lesson_pointers(["Not A Real Area"])
    assert pointers == {"lesson_signatures": [], "lesson_docs": []}
    assert unknown == ["Not A Real Area"]


def test_format_lesson_pointers_renders_yaml_like_block():
    text = format_lesson_pointers(
        {
            "lesson_signatures": ["orbit-animated-texture-strip"],
            "lesson_docs": ["docs/render-types.md"],
        }
    )
    assert "lesson_signatures:" in text
    assert "  - orbit-animated-texture-strip" in text
    assert "lesson_docs:" in text
    assert "  - docs/render-types.md" in text


def test_main_lessons_flag_prints_pointers():
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["--lessons", "Render Preview"])
    assert code == 0
    out = buf.getvalue()
    assert "orbit-animated-texture-strip" in out
    assert "docs/render-types.md" in out


def test_main_lessons_unknown_label_exits_nonzero():
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["--lessons", "Not A Real Area"])
    assert code == 1


REFERENCE_LESSONS_BY_AREA = """## Lessons by area (read before card grep)

| Signal / Feature Area | Read first |
| --------------------- | ---------- |
| **Render Preview** — animated lit fronts | docs |
"""


def test_parse_agents_governance_keys_valid():
    skill, rules, routing = parse_agents_governance_keys(
        {
            "agents_skill": "ui-change",
            "agents_rules": ["ui-panels.mdc", "testing.mdc#orbit-animated-texture-strip"],
            "lesson_routing_row": "Render Preview",
        }
    )
    assert skill == "ui-change"
    assert rules == ("ui-panels.mdc", "testing.mdc#orbit-animated-texture-strip")
    assert routing == "Render Preview"


def test_parse_agents_governance_keys_invalid_rules_type():
    skill, rules, routing = parse_agents_governance_keys(
        {
            "agents_skill": "agent-triage",
            "agents_rules": "agent-routing.mdc",
            "lesson_routing_row": None,
        }
    )
    assert skill == "agent-triage"
    assert rules == ()
    assert routing is None


def test_lessons_by_area_row_found_matches_reference():
    assert lessons_by_area_row_found("Render Preview", REFERENCE_LESSONS_BY_AREA) is True
    assert lessons_by_area_row_found("Not In Table", REFERENCE_LESSONS_BY_AREA) is False
    assert lessons_by_area_row_found(None, REFERENCE_LESSONS_BY_AREA) is None


def test_resolve_agents_parity_render_preview():
    infos, unknown = resolve_agents_parity(
        ["Render Preview"],
        reference_text=REFERENCE_LESSONS_BY_AREA,
    )
    assert not unknown
    assert len(infos) == 1
    info = infos[0]
    assert info.agents_skill == "ui-change"
    assert "ui-panels.mdc" in info.agents_rules
    assert info.lesson_routing_row == "Render Preview"
    assert info.lessons_by_area_row_found is True


def test_agents_parity_load_schema_valid_fixture():
    yaml_text = """
areas:
  Seeded Area:
    agents_skill: ui-change
    agents_rules:
      - ui-panels.mdc
    lesson_routing_row: Render Preview
    lesson_signatures:
      - orbit-animated-texture-strip
"""
    entries = load_area_schema_entries(yaml_text)
    assert len(entries) == 1
    assert entries[0].agents_skill == "ui-change"
    assert entries[0].lesson_routing_row == "Render Preview"


def test_agents_parity_load_schema_invalid_missing_routing_row(tmp_path):
    (tmp_path / ".cursor/skills/ui-change").mkdir(parents=True)
    (tmp_path / ".cursor/skills/ui-change/SKILL.md").write_text("# skill\n", encoding="utf-8")
    issues = check_area_schema_parity(
        tmp_path,
        [
            AreaSchemaEntry(
                name="Bad Area",
                agents_skill="ui-change",
                agents_rules=(),
                lesson_routing_row="Missing Row",
                lesson_signatures=(),
            )
        ],
        REFERENCE_LESSONS_BY_AREA,
        "areas: {}\n",
        set(),
    )
    assert len(issues) == 1
    assert "lesson_routing_row" in issues[0]


def test_format_agents_parity_renders_expected_fields():
    text = format_agents_parity(
        AgentsParityInfo(
            label="Render Preview",
            agents_skill="ui-change",
            agents_rules=("ui-panels.mdc",),
            lesson_routing_row="Render Preview",
            lessons_by_area_row_found=True,
        )
    )
    assert "agents_skill: ui-change" in text
    assert "  - ui-panels.mdc" in text
    assert "lesson_routing_row: Render Preview" in text
    assert "lessons_by_area_row: found" in text


def test_main_agents_parity_flag_prints_fields():
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["--agents-parity", "Render Preview"])
    assert code == 0
    out = buf.getvalue()
    assert "agents_skill: ui-change" in out
    assert "lesson_routing_row: Render Preview" in out
    assert "lessons_by_area_row: found" in out


def test_main_agents_parity_unknown_label_exits_nonzero():
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["--agents-parity", "Not A Real Area"])
    assert code == 1
