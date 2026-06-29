"""Tests for scripts/resolve_card_tests.py (pre-commit hook simulation)."""

from __future__ import annotations

from pathlib import Path

from scripts.resolve_card_tests import (
    extract_product_paths,
    parse_targeted_files,
    simulate_hook,
)


def test_sprite_baker_path_includes_cache_test():
    code, output = simulate_hook(["helpers/sprite_baker/compose_stairs.py"])
    assert code == 0
    assert "test_sprite_baker_cache.py" in output
    files = parse_targeted_files(output)
    assert "tests/test_sprite_baker_cache.py" in files


def test_parse_targeted_files_empty_on_full_suite():
    output = "pre-commit pytest: full suite (core or global change detected)\n"
    assert parse_targeted_files(output) == []


def test_extract_product_paths_from_card(tmp_path: Path):
    card = tmp_path / "feature.md"
    card.write_text(
        """---
labels: ["feature"]
---
# Example

## Product Paths

- `helpers/cells.py`
- `ui/main_window.py`

## Tests

### Files

- `tests/test_other.py`
""",
        encoding="utf-8",
    )
    paths = extract_product_paths(card.read_text(encoding="utf-8"))
    assert paths == ["helpers/cells.py", "ui/main_window.py"]


def test_from_card_resolves_done_bucket(tmp_path: Path, monkeypatch):
    features = tmp_path / "features"
    done = features / "done"
    done.mkdir(parents=True)
    card = done / "closed-feature.md"
    card.write_text(
        """---
labels: ["feature"]
---
# Example

## Product Paths

- `helpers/cells.py`
""",
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.move_kanban_card.DEFAULT_FEATURES_DIR", features)

    from scripts.resolve_card_tests import main

    code = main(["--from-card", "closed-feature", "--files-only"])
    assert code == 0
