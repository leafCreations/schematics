from scripts.resolve_prior_lessons import (
    _lessons_excerpt,
    _section_body_aliases,
    area_artifacts,
    extract_label_paths,
    find_done_lessons,
)


def test_lessons_excerpt_returns_body_after_heading():
    text = "## Lessons captured (2026-06-25)\n\n- **Fix:** frame 0 only.\n\n## Verify\n"
    excerpt = _lessons_excerpt(text)
    assert excerpt is not None
    assert "frame 0" in excerpt
    assert "Verify" not in excerpt


def test_find_done_lessons_matches_epic(tmp_path, monkeypatch):
    done_dir = tmp_path / "done"
    done_dir.mkdir()
    card = done_dir / "sample-done.md"
    card.write_text(
        "---\nepic: TestEpic\n---\n\n## Lessons captured (2026-06-25)\n\n- lesson one\n",
        encoding="utf-8",
    )

    import scripts.resolve_prior_lessons as mod

    monkeypatch.setattr(mod, "DONE_DIR", done_dir)
    monkeypatch.setattr(mod, "ARCHIVED_DIR", tmp_path / "archived")

    hits = find_done_lessons(epic="TestEpic", labels=[], path_prefixes=[])
    assert len(hits) == 1
    assert "lesson one" in hits[0][1]


def test_find_done_lessons_includes_archived(tmp_path, monkeypatch):
    archived_dir = tmp_path / "archived"
    archived_dir.mkdir()
    card = archived_dir / "old-feature.md"
    card.write_text(
        "---\nepic: LegacyEpic\n---\n\n## Lessons captured (2026-06-20)\n\n- archived lesson\n",
        encoding="utf-8",
    )

    import scripts.resolve_prior_lessons as mod

    monkeypatch.setattr(mod, "DONE_DIR", tmp_path / "done")
    monkeypatch.setattr(mod, "ARCHIVED_DIR", archived_dir)

    hits = find_done_lessons(epic="LegacyEpic", labels=[], path_prefixes=[])
    assert len(hits) == 1
    assert "archived lesson" in hits[0][1]


def test_area_artifacts_lists_docs():
    artifacts = area_artifacts(["Render Preview"])
    assert "docs/ui.md" in artifacts["docs"]


def test_section_body_aliases_prefers_first_heading():
    text = "## Product Paths\n\n- `ui/foo.py`\n\n## Label Paths\n\n- `ui/bar.py`\n"
    body = _section_body_aliases(text, ("Product Paths", "Label Paths"))
    assert body is not None
    assert "`ui/foo.py`" in body
    assert "`ui/bar.py`" not in body


def test_extract_label_paths_reads_product_paths():
    text = "## Product Paths\n\n- `helpers/cells.py`\n"
    assert extract_label_paths(text) == ["helpers/cells.py"]


def test_extract_label_paths_legacy_label_paths():
    text = "## Label Paths\n\n- `helpers/cells.py`\n"
    assert extract_label_paths(text) == ["helpers/cells.py"]


def test_extract_label_paths_includes_tests_files():
    text = (
        "## Product Paths\n\n- `helpers/cells.py`\n\n"
        "## Tests\n\n### Files\n\n- `tests/test_cells.py`\n\n### Methods\n\n- _TBD_\n"
    )
    assert extract_label_paths(text) == ["helpers/cells.py", "tests/test_cells.py"]
