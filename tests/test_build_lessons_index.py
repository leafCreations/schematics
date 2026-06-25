from scripts.build_lessons_index import (
    build_index,
    index_is_current,
    map_card_to_areas,
    render_index_yaml,
    write_index,
)
from scripts.resolve_prior_lessons import (
    ParsedArtifacts,
    _normalize_doc_ref,
    extract_feature_area_labels,
    extract_governance_artifacts,
    extract_signatures,
    parse_artifacts_line,
)


def test_parse_artifacts_line_expands_typed_entries():
    line = (
        "  - artifacts: skill:project-context, "
        "rule:testing.mdc#orbit-animated-texture-strip, "
        "doc:render-types.md, sig:orbit-animated-texture-strip, "
        "test:tests/test_block_texture_load.py"
    )
    parsed = parse_artifacts_line(line)
    assert parsed.skills == [".cursor/skills/project-context/SKILL.md"]
    assert parsed.rules == [".cursor/rules/testing.mdc"]
    assert parsed.docs == ["docs/render-types.md"]
    assert parsed.signatures == ["orbit-animated-texture-strip"]
    assert parsed.tests == ["tests/test_block_texture_load.py"]
    assert parsed.repo_paths() == [
        ".cursor/skills/project-context/SKILL.md",
        ".cursor/rules/testing.mdc",
        "docs/render-types.md",
        "tests/test_block_texture_load.py",
    ]


def test_parse_artifacts_line_empty_when_no_match():
    assert parse_artifacts_line("- **Fix:** only prose") == ParsedArtifacts()


def test_parse_artifacts_line_doc_yaml_registry_paths():
    parsed = parse_artifacts_line("  - artifacts: doc:lessons-index.yaml, doc:feature-areas.yaml")
    assert parsed.docs == [
        "docs/lessons-index.yaml",
        "docs/feature-areas.yaml",
    ]


def test_parse_artifacts_line_doc_preserves_md_legacy_basename():
    parsed = parse_artifacts_line("  - artifacts: doc:render-types.md, doc:render-types")
    assert parsed.docs == ["docs/render-types.md"]


def test_normalize_doc_ref_accepts_yaml_and_docs_prefix():
    assert _normalize_doc_ref("lessons-index.yaml") == "docs/lessons-index.yaml"
    assert _normalize_doc_ref("feature-areas.yaml") == "docs/feature-areas.yaml"
    assert _normalize_doc_ref("docs/lessons-index.yaml") == "docs/lessons-index.yaml"
    assert _normalize_doc_ref("render-types.md") == "docs/render-types.md"
    assert _normalize_doc_ref("render-types") == "docs/render-types.md"
    assert _normalize_doc_ref("lessons-index") is None


def test_parse_artifacts_line_doc_skips_extensionless_yaml_registry():
    parsed = parse_artifacts_line("  - artifacts: doc:lessons-index, doc:development.md")
    assert parsed.docs == ["docs/development.md"]


def test_extract_governance_artifacts_prefers_artifacts_line():
    lessons = (
        "- **Symptom:** holes in preview\n"
        "- **Fix:** use frame 0\n"
        "  - artifacts: skill:repo-map, rule:testing.mdc, doc:render-types.md\n"
        "- **Governance:** `.cursor/rules/ui-panels.mdc` (ignored when artifacts present)\n"
    )
    artifacts = extract_governance_artifacts(lessons)
    assert artifacts == [
        ".cursor/skills/repo-map/SKILL.md",
        ".cursor/rules/testing.mdc",
        "docs/render-types.md",
    ]


def test_extract_signatures_from_artifacts_sig_prefix():
    lessons = (
        "- **Fix:** tile frame 0\n"
        "  - artifacts: sig:orbit-animated-texture-strip, rule:testing.mdc\n"
    )
    assert extract_signatures(lessons) == ["orbit-animated-texture-strip"]


def test_build_index_uses_artifacts_line(tmp_path, monkeypatch):
    done_dir = tmp_path / ".devtool" / "features" / "done"
    done_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    registry = docs_dir / "feature-areas.yaml"
    registry.write_text(
        "areas:\n  Render Preview:\n    paths:\n      - helpers/orbit_face_textures.py\n",
        encoding="utf-8",
    )

    card = done_dir / "artifacts-sample.md"
    card.write_text(
        "---\n---\n\n"
        "## Feature Areas\n\n`Render Preview`\n\n"
        "## Lessons captured (2026-06-25)\n\n"
        "- **Symptom:** animated strip in tests\n"
        "- **Fix:** load_block_texture_image frame 0\n"
        "  - artifacts: skill:project-context, rule:testing.mdc, "
        "doc:render-types.md, sig:orbit-animated-texture-strip, "
        "test:tests/test_block_texture_load.py\n",
        encoding="utf-8",
    )

    import scripts.build_lessons_index as build_mod
    import scripts.resolve_prior_lessons as lessons_mod

    archived_dir = tmp_path / ".devtool" / "features" / "archived"
    monkeypatch.setattr(lessons_mod, "DONE_DIR", done_dir)
    monkeypatch.setattr(lessons_mod, "ARCHIVED_DIR", archived_dir)
    monkeypatch.setattr(lessons_mod, "REGISTRY_PATH", registry)
    monkeypatch.setattr(build_mod, "REGISTRY_PATH", registry)

    payload = build_index(repo_root=tmp_path)
    area = payload["areas"]["Render Preview"]
    assert area["signatures"] == ["orbit-animated-texture-strip"]
    assert area["artifacts"] == [
        ".cursor/rules/testing.mdc",
        ".cursor/skills/project-context/SKILL.md",
        "docs/render-types.md",
        "tests/test_block_texture_load.py",
    ]

    text = "**Governance:** `.cursor/rules/testing.mdc` Signature `orbit-animated-texture-strip`"
    assert extract_signatures(text) == ["orbit-animated-texture-strip"]


def test_extract_signatures_from_lesson_heading():
    text = "- **`precommit-mainwindow-__new__-test`:** guard optional panel"
    assert extract_signatures(text) == ["precommit-mainwindow-__new__-test"]


def test_extract_governance_artifacts_normalizes_relative_links():
    lessons = (
        "- **Governance:** [testing.mdc](../../.cursor/rules/testing.mdc) "
        "Signature `orbit-fence-mask-transparency`; "
        "`docs/render-types.md` § Orbit partial blocks"
    )
    artifacts = extract_governance_artifacts(lessons)
    assert ".cursor/rules/testing.mdc" in artifacts
    assert "docs/render-types.md" in artifacts


def test_map_card_to_areas_uses_feature_areas_label():
    text = "## Feature Areas\n\n`Render Preview`\n"
    registry = {"Render Preview": {"paths": ["helpers/orbit_face_textures.py"]}}
    assert map_card_to_areas(text, registry) == ["Render Preview"]


def test_map_card_to_areas_falls_back_to_unique_label_paths():
    text = "## Label Paths\n\n- `helpers/orbit_partial_mesh.py`\n"
    registry = {
        "Render Preview": {"paths": ["helpers/orbit_partial_mesh.py"]},
    }
    assert map_card_to_areas(text, registry) == ["Render Preview"]


def test_map_card_to_areas_uses_unique_label_path_owner():
    text = "## Label Paths\n\n- `ui/widgets/properties_panel.py`\n"
    registry = {
        "Properties Panel": {"paths": ["ui/widgets/properties_panel.py"]},
        "Render Panel": {"paths": ["ui/main_window.py"]},
    }
    assert map_card_to_areas(text, registry) == ["Properties Panel"]


def test_map_card_to_areas_skips_ambiguous_shared_paths():
    text = "## Label Paths\n\n- `ui/main_window.py`\n"
    registry = {
        "File Menu": {"paths": ["ui/main_window.py"]},
        "View Menu": {"paths": ["ui/main_window.py"]},
    }
    assert map_card_to_areas(text, registry) == ["_uncategorized"]


def test_map_card_to_areas_uncategorized_when_no_match():
    assert map_card_to_areas("## Label Paths\n\n- `unknown/path.py`\n", {}) == ["_uncategorized"]


def test_extract_feature_area_labels_singular_heading():
    text = "## Feature Area\n\n- `Agent Workflow`\n"
    assert extract_feature_area_labels(text) == ["Agent Workflow"]


def test_build_index_ignores_decisions_placeholder_signatures(tmp_path, monkeypatch):
    done_dir = tmp_path / ".devtool" / "features" / "done"
    done_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    registry = docs_dir / "feature-areas.yaml"
    registry.write_text(
        "areas:\n  Agent Workflow:\n    paths:\n      - AGENTS.md\n",
        encoding="utf-8",
    )
    card = done_dir / "placeholder.md"
    card.write_text(
        "---\n---\n\n"
        "## Feature Area\n\n`Agent Workflow`\n\n"
        "## Decisions\n\n"
        "Uses Signature `…` grep from card text (placeholder, not a real signature).\n\n"
        "## Lessons captured (2026-06-25)\n\n"
        "- **Governance:** `.cursor/rules/testing.mdc`\n",
        encoding="utf-8",
    )

    import scripts.build_lessons_index as build_mod
    import scripts.resolve_prior_lessons as lessons_mod

    archived_dir = tmp_path / ".devtool" / "features" / "archived"
    monkeypatch.setattr(lessons_mod, "DONE_DIR", done_dir)
    monkeypatch.setattr(lessons_mod, "ARCHIVED_DIR", archived_dir)
    monkeypatch.setattr(lessons_mod, "REGISTRY_PATH", registry)
    monkeypatch.setattr(build_mod, "REGISTRY_PATH", registry)

    payload = build_index(repo_root=tmp_path)
    assert payload["areas"]["Agent Workflow"]["signatures"] == []


def test_build_index_groups_lesson_card(tmp_path, monkeypatch):
    done_dir = tmp_path / ".devtool" / "features" / "done"
    done_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    registry = docs_dir / "feature-areas.yaml"
    registry.write_text(
        "areas:\n  Render Preview:\n    paths:\n      - helpers/orbit_face_textures.py\n",
        encoding="utf-8",
    )

    card = done_dir / "sample-done.md"
    card.write_text(
        "---\nepic: RenderEngine\n---\n\n"
        "## Feature Areas\n\n`Render Preview`\n\n"
        "## Lessons captured (2026-06-25)\n\n"
        "- **Governance:** `.cursor/rules/testing.mdc` "
        "Signature `orbit-animated-texture-strip`\n",
        encoding="utf-8",
    )

    import scripts.build_lessons_index as build_mod
    import scripts.resolve_prior_lessons as lessons_mod

    archived_dir = tmp_path / ".devtool" / "features" / "archived"
    monkeypatch.setattr(lessons_mod, "DONE_DIR", done_dir)
    monkeypatch.setattr(lessons_mod, "ARCHIVED_DIR", archived_dir)
    monkeypatch.setattr(lessons_mod, "REGISTRY_PATH", registry)
    monkeypatch.setattr(build_mod, "REGISTRY_PATH", registry)

    payload = build_index(repo_root=tmp_path)
    area = payload["areas"]["Render Preview"]
    rel = ".devtool/features/done/sample-done.md"
    assert area["done_cards"] == [rel]
    assert area["signatures"] == ["orbit-animated-texture-strip"]
    assert area["artifacts"] == [".cursor/rules/testing.mdc"]


def test_build_index_empty_when_devtool_missing(tmp_path):
    payload = build_index(repo_root=tmp_path)
    assert payload["areas"] == {}


def test_index_is_current_detects_stale(tmp_path):
    output = tmp_path / "lessons-index.yaml"
    payload = {"version": 1, "generated_at": "2026-06-25T00:00:00+00:00", "areas": {}}
    write_index(payload, output_path=output)
    payload["generated_at"] = "2026-06-25T12:00:00+00:00"
    assert not index_is_current(payload, output_path=output)


def test_render_index_yaml_includes_generated_header():
    rendered = render_index_yaml({"version": 1, "generated_at": "t", "areas": {}})
    assert rendered.startswith("# Generated by scripts/build_lessons_index.py")
