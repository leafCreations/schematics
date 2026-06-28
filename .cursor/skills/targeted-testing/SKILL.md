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

**Do not** create `.tmp-venv` or other throwaway venvs in the repo (Signature:
`agent-no-tmp-venv`). If `.venv` is missing, ask the user to run
`python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"` — or run that once
with user approval — then use `.venv/bin/pytest`.

## Workflow

### 1. Identify changed paths

Use `git diff --name-only` (staged or working tree) or the files you just edited.

### 2. Map paths → tests

| Priority | Source |
| -------- | ------ |
| 1 | [reference.md](reference.md) quick table |
| 2 | `scripts/pre-commit-pytest.sh` `case` branches (source of truth) |
| 3 | Convention: `helpers/foo.py` → `tests/test_foo.py` if it exists |
| 4 | Kanban card **`## Tests`** — **Files** and **Methods**; **`## Product Methods`** for code symbols |
| 5 | [repo-map](../repo-map/SKILL.md) entry points |

**Docs-only** (`docs/**`) with no code changes → **no pytest**.

**Before Review (mandatory — Signature: `precommit-pytest-scope-mismatch`):**

1. Draft **Tests → Files** from **Product Paths** (not only the test adjacent to your edit):

   ```bash
   python3 scripts/resolve_card_tests.py --from-card .devtool/features/your-card.md --files-only
   # or: python3 scripts/resolve_card_tests.py helpers/sprite_baker/foo.py --files-only
   ```

   Hook SSOT: `scripts/pre-commit-pytest.sh` `case` branches — the helper simulates them via
   `PRE_COMMIT_PYTEST_LIST_ONLY=1`.

2. Stage intended commit paths; run **`scripts/pre-commit-pytest.sh`** (same as commit hook) or
   **`scripts/agent-commit-ready.sh`** (ruff → palettes → pytest on staged files).

3. Cross-check card **Tests → Files** against hook output for targeted runs; **Tests → Verify (agent)**
   must cite `scripts/pre-commit-pytest.sh`. When hook says **full suite**, **Verify** cites
   `.venv/bin/pytest -q`.

4. Optional behavior invariants (e.g. grep `STAIRS` + `== 0` after compositor changes) belong in
   **Tests**, not **Acceptance Criteria** — Signature: `2d-stair-riser-runtime-cache-test`.

**Test file edited** → run **that file** (and only add related files if the test imports shared fixtures you changed).

**Lessons coverage audit (lc1 / lc4c / lc4b):** after edits under `scripts/check_lessons_coverage.py`,
`scripts/lessons_coverage_lib.py`, or `scripts/resolve_prior_lessons.py`:

```bash
.venv/bin/pytest tests/test_check_lessons_coverage.py tests/test_check_governance_parity.py tests/test_resolve_prior_lessons.py -q
```

Include `test_check_governance_parity.py` when drift spawn body changes
(`build_drift_card_body` / `_spawn_review_sections`). **C1b / five-metric composite:** adding a
sub-metric changes drift severity fixtures — grep `test_check_lessons_coverage_drift_critical` and
update label-scoped done-card frontmatter in fixtures. **C4 per-card (lc4b):** composite and 75%
drift gate use `audit_application_coverage_per_card`; aggregate C4 is advisory — grep
`test_c4_per_card_passes_when_aggregate_low` and `test_drift_threshold_follows_per_card_c4`.
**Parser SSOT:** `PRIOR_LESSONS_RE` lives in
`resolve_prior_lessons.py` only — `lessons_coverage_lib` imports `extract_prior_lessons_citations`.
Signature: `lessons-coverage-c1b-forward-feedback`, `lessons-coverage-c2-c3-audit`,
`lessons-coverage-c4-per-card-threshold` — see
[reference.md](reference.md) and [testing.mdc](../../rules/testing.mdc).

**Forward feedback index (ff0):** after edits under `scripts/build_forward_feedback_index.py`,
`scripts/resolve_forward_feedback.py`, or gc5 item parsers in `scripts/lessons_coverage_lib.py`:

```bash
.venv/bin/pytest tests/test_build_forward_feedback_index.py tests/test_resolve_forward_feedback.py -q
```

Signature: `forward-feedback-index` — see [testing.mdc](../../rules/testing.mdc).

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

### 5. Before commit — match pre-commit scope (mandatory)

**Do not** rely on “I ran some tests earlier.” Re-verify against **staged** paths right before commit.

Hook order: **ruff** → palettes → pytest ([pre-commit-workflow](../pre-commit-workflow/SKILL.md)).

0. **Ruff E501** on every touched `.py`/`.pyi` before handoff or commit:

   ```bash
   .venv/bin/ruff check --select E501 path/to/edited.py
   ```

   Signature: `ruff-e501-line-length` — not optional on implementation turns.

**Commit-issue cards:** manual runs of this script or `scripts/pre-commit-pytest.sh` do **not** create kanban cards — only failed **`git commit`** hooks do (`PRE_COMMIT=1`). Fix pytest failures in-session; Signature: `precommit-no-card-on-manual-hook`.

1. `git diff --cached --name-only` — list what will be committed.
2. Run the hook script (same selection logic as commit):

   ```bash
   scripts/pre-commit-pytest.sh
   ```

   Read the first line of output:

   | Output | Run |
   | ------ | --- |
   | `full suite (core or global change detected)` | `.venv/bin/pytest -q` |
   | `full suite (…)` (other reasons) | `.venv/bin/pytest -q` |
   | `N file(s) — test_…` | those files only |
   | `skipped (no mapped code changes)` | no pytest |

3. If the script exits non-zero, fix → re-run **the same scope** (not a smaller subset) until green.
4. Optional after green on staged hash:

   ```bash
   scripts/record-pytest-pass.sh
   ```

Pre-commit may skip pytest for 30 minutes for the same staged hash. Ruff and palette checks still run. Full hook order: [pre-commit-workflow](../pre-commit-workflow/SKILL.md).

### 6. After fixes — re-evaluate scope (common agent gap)

When you change code **because a test failed**, the right re-run is often **broader** than the single failing file:

| You fixed | Also re-run (if staged or related) |
| --------- | ---------------------------------- |
| `registries/palettes/*.yaml` moved blocks between tabs | `test_palette_integrity`, `test_block_picker`, `test_sprite_baker_simple`, `test_registry_phase_b` |
| `helpers/terrain_tokens.py` / natural vs terrain split | `test_terrain_tokens`, `test_sprite_baker_simple` |
| `structures/**` layer YAML (beds, chests, tokens) | `test_worldgen_functional_blocks`, `test_structure_loader` |
| `render_main.py` or `registries/loader.py` staged | **full suite** (hook forces it) |
| `helpers/sprite_baker/*` compositor semantic change (e.g. riser ghost α) | `test_sprite_baker_cache.py` — hook maps all `helpers/sprite_baker/*`; grep `tests/` for stale `STAIRS` + `== 0` — Signature: `2d-stair-riser-runtime-cache-test`, `precommit-pytest-scope-mismatch` |
| Any `tests/test_*.py` edited | that file + tests that import the same fixtures |

**Rule:** after a fix, run `scripts/pre-commit-pytest.sh` again — not only `pytest failed_file.py`.

### 7. After green run (commit prep)

If staged files match what you tested, `scripts/record-pytest-pass.sh` (see §5).

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
| `helpers/orbit_*.py`, `ui/widgets/orbit_preview_widget.py`, `ui/mesh_build_worker.py` | `tests/test_orbit_greedy_mesh.py` `tests/test_orbit_partial_mesh.py` `tests/test_orbit_preview.py` |
| `helpers/sprite_baker/compose_bed.py`, `helpers/paths.py` (`resolve_entity_bed_textures_folder`), colored `BED:*` orbit faces, merged bed part split (`_iter_bed_face_parts`, `bed_foot_token`) | `pytest tests/test_orbit_greedy_mesh.py tests/test_sprite_baker_bed.py -q -k bed` — Signature: `orbit-bed-colored-texture-keys` |
| `structures/**` | `tests/test_structure_loader.py` `tests/test_ui_document.py` |

Full list: [reference.md](reference.md).

## Writing tests — avoid catalog churn

**Do not** hard-code terrain palette **block counts** (e.g. `assert count == 32`). Minecraft version and catalog updates change totals.

Prefer:

- `assert "minecraft:stone" in tokens`
- `assert "WALL" in tokens` + `enumerate_token_materials("minecraft:{material}_wall")` for templated families — **not** raw `minecraft:*_wall` in palette `blocks:`
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
scripts/pre-commit-pytest.sh    # runs hook for real (requires staged files)
```

Draft **Tests → Files** from **Product Paths** before Review (no staging required):

```bash
python3 scripts/resolve_card_tests.py --from-card .devtool/features/your-card.md --files-only
python3 scripts/resolve_card_tests.py helpers/sprite_baker/foo.py --files-only
```

Uses `PRE_COMMIT_PYTEST_LIST_ONLY=1` against `scripts/pre-commit-pytest.sh` — Signature:
`precommit-pytest-scope-mismatch`.

Or run all three hooks on staged paths:

```bash
scripts/agent-commit-ready.sh
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
