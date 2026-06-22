---
name: targeted-testing
description: >-
  Pick and run the smallest pytest set for structure_scripts changes. Use when
  verifying edits, fixing test failures, before commit, after pre-commit pytest
  fails, or when the user asks to run tests — not for full-suite optimization
  (use optimize-test-suite instead).
---

# Targeted Testing

Run the **smallest meaningful pytest set** for what you changed. Default is **not** the full suite.

Pair with [agent-triage](../agent-triage/SKILL.md) for when to test; this skill is **which tests** and **how to run them**.

## Before every pytest run

State one line in your response:

```text
Running: <test paths> — because <changed files / behavior>
```

Use `.venv/bin/pytest` from repo root (or `pytest` if venv active).

## Workflow

### 1. Identify changed paths

Use `git diff --name-only` (staged or working tree) or the files you just edited.

### 2. Map paths → tests

| Priority | Source |
| -------- | ------ |
| 1 | [reference.md](reference.md) quick table |
| 2 | `scripts/pre-commit-pytest.sh` `case` branches (source of truth) |
| 3 | Convention: `helpers/foo.py` → `tests/test_foo.py` if it exists |
| 4 | [repo-map](../repo-map/SKILL.md) entry points |

**Docs-only** (`docs/**`) with no code changes → **no pytest**.

**Test file edited** → run **that file** (and only add related files if the test imports shared fixtures you changed).

### 3. Run targeted tests

```bash
.venv/bin/pytest tests/test_block_picker.py tests/test_palette_integrity.py -q
```

Options:

- `-q` — quiet (default for agent runs)
- `-x` — stop on first failure (good while fixing)
- `::test_name` — single test when isolating one failure

### 4. On failure

1. Summarize the failure in one sentence.
2. Fix the likely source file.
3. Re-run **failed test file only** (or `::test_name`).
4. Broaden only if the fix touched shared infrastructure.

**Do not** re-run the same failing test three times without a code or analysis change.

### 5. After green run (commit prep)

If staged files match what you tested:

```bash
scripts/record-pytest-pass.sh
```

Pre-commit may skip pytest for 30 minutes for the same staged hash. Ruff and palette checks still run. Full hook order: [pre-commit-workflow](../pre-commit-workflow/SKILL.md).

## When to run the full suite

Run `pytest` or `pre-commit run pytest --all-files` only when:

| Trigger | Example |
| ------- | ------- |
| User asks before PR | "run full tests" |
| Core wiring changed | `conftest.py`, `registries/loader.py`, `render_main.py`, `helpers/context.py` |
| Pre-commit chose full suite | Hook output says "full suite" |
| Targeted pass but high risk | Many packages touched; unclear dependency graph |
| Test infra changed | `pyproject.toml` pytest config |

Pre-commit also runs **full suite** when:

- More than **20** targeted test files would run (`MAX_TARGETED` in script)
- Staged `*.py` is **unmapped** in the script (falls through to `CODE_TOUCHED` with empty test list)

## Common mappings (manual edits)

| Changed | Run |
| ------- | --- |
| `helpers/block_picker.py` | `tests/test_block_picker.py` `tests/test_palette_integrity.py` |
| `helpers/materials.py` | `tests/test_materials.py` |
| `helpers/structure_loader.py` | `tests/test_structure_loader.py` `tests/test_ui_document.py` |
| `helpers/path_geometry.py` | `tests/test_path_geometry.py` |
| `registries/**` | `tests/test_palette_integrity.py` `tests/test_registry_phase_b.py` |
| `ui/document.py` | `tests/test_ui_document.py` |
| `ui/widgets/palette_panel.py` | `tests/test_palette_panel.py` |
| `ui/main_window.py` | `tests/test_main_window.py` |
| `renderers/worldgen.py` | `tests/test_worldgen_bed.py` `tests/test_worldgen_site.py` … (see reference) |
| `structures/**` | `tests/test_structure_loader.py` `tests/test_ui_document.py` |

Full list: [reference.md](reference.md).

## Writing tests — avoid catalog churn

**Do not** hard-code terrain palette **block counts** (e.g. `assert count == 32`). Minecraft version and catalog updates change totals.

Prefer:

- `assert "minecraft:stone" in tokens`
- `tests/palette_helpers.py` → `terrain_section_entry_counts()`
- `assert panel._block_list.count() == section_counts["overworld"]`

## Qt / UI tests

PySide6 tests may **segfault in sandboxed** agent shells. If pytest dies with SIGSEGV on `tests/test_*panel*.py` or `test_main_window.py`:

- Re-run with full permissions, or
- Run that file locally and report result

One `QApplication` per module scope is already used in UI tests — do not spawn extra app fixtures.

## Heavy / asset tests

Tests marked `@pytest.mark.requires_assets` need `assets/minecraft/textures/block/`. Skip is OK in CI-less environments; do not fail the task if skip is expected.

## Simulate pre-commit selection

To see which tests the hook would run on staged files:

```bash
git diff --cached --name-only   # review staged paths
# Match against scripts/pre-commit-pytest.sh cases
pre-commit run pytest           # runs hook for real
```

Or run the script directly (requires staged files):

```bash
scripts/pre-commit-pytest.sh
```

## Do not use this skill for

| Task | Use instead |
| ---- | ----------- |
| Consolidating redundant tests | [optimize-test-suite](../optimize-test-suite/SKILL.md) |
| Profiling slow tests | optimize-test-suite |
| "Review entire test suite" | optimize-test-suite |

## Checklist

```
- [ ] Changed paths identified
- [ ] Test list stated before run
- [ ] Smallest set chosen (not full suite by default)
- [ ] Failures fixed with targeted re-runs
- [ ] record-pytest-pass.sh after green staged run (optional)
```

Extended mapping: [reference.md](reference.md).
