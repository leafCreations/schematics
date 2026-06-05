---
name: optimize-test-suite
description: >-
  Reviews test suites, consolidates redundant tests, and speeds up pytest runs.
  Use when the user asks to review tests, consolidate tests, speed up tests,
  reduce test duration, optimize the test suite, or improve test performance.
disable-model-invocation: true
---

# Optimize Test Suite

Systematically review tests, merge overlap safely, and shorten total runtime without losing meaningful coverage.

## Goals (in order)

1. **Keep behavior coverage** — do not delete tests that guard distinct failures.
2. **Consolidate redundancy** — one test per behavior, not per permutation of setup.
3. **Speed up execution** — fixtures, I/O, imports, and suite structure.

## Phase 1 — Baseline

Run before any edits. Record numbers for the final report.

```bash
# Full suite duration (use project venv if present)
.venv/bin/pytest --durations=20 -q 2>&1 | tee /tmp/pytest-baseline.txt

# Optional: per-file timings
.venv/bin/pytest --durations=0 -q 2>&1 | tail -30
```

If `.cursor/skills/optimize-test-suite/scripts/profile-tests.sh` exists in the repo, run it instead.

Read project config first: `pyproject.toml` (`[tool.pytest.ini_options]`), `tests/conftest.py`, `.cursor/rules/testing.mdc`, and any `scripts/pre-commit-pytest.sh` path mappings.

## Phase 2 — Inventory

Build a mental map of the suite:

| Bucket | What to look for |
| ------ | ---------------- |
| **Unit** | Pure logic, no disk/network/GUI |
| **Integration** | Loaders, pipelines, multi-module flows |
| **Heavy** | Real assets, image bake, worldgen, Qt/UI |
| **Smoke** | Integrity / round-trip / registry validation |

For each slow test (top `--durations` entries), note **why** it is slow: fixture scope, asset load, subprocess, sleep, redundant setup.

## Phase 3 — Consolidation candidates

Merge only when assertions cover the **same contract**. Prefer these patterns:

### Parametrize instead of copy-paste

```python
# Before: three functions with identical structure
# After:
@pytest.mark.parametrize(
    ("raw", "expected"),
    [("A", 1), ("B", 2), (".", 0)],
)
def test_count_blocks(raw, expected):
    assert count_blocks([[raw]]) == expected
```

### One test, multiple cases via `ids`

Use when cases need short names in failure output.

### Merge files only when they test the same module

Example: `test_foo_edge.py` + `test_foo_basic.py` → `test_foo.py` with sections. **Do not** merge unrelated domains to shrink file count.

### Shared setup → fixture

Lift repeated 5+ line setup into `conftest.py` or a module fixture. Widen scope only when safe (see Phase 4).

### Do NOT consolidate

- Tests that fail for **different reasons** (keep separate).
- Tests documenting distinct regression bugs (keep name/story).
- Assertions that differ in **expected exception type** or side effects.

## Phase 4 — Performance fixes

Apply highest impact first:

| Technique | When |
| --------- | ---- |
| `scope="session"` fixture | Expensive read-only setup (registry load, catalog build) shared across tests |
| `scope="module"` fixture | Medium setup reused in one file |
| `tmp_path` / minimal fakes | Instead of `assets/minecraft/` or large structures |
| `@pytest.mark.requires_assets` | Gate heavy tests; document in `conftest.py` |
| Lazy import inside test/fixture | Optional deps (PySide6, amulet) not needed for whole session |
| Remove `autouse=True` | Unless every test in scope truly needs it |
| `monkeypatch` / `mocker` | Prefer over real subprocess or disk where contract allows |
| `-n auto` (pytest-xdist) | Only suggest if project already depends on xdist; do not add deps unless user asks |
| `pytest.importorskip` | Skip UI/worldgen tests when extras not installed |

### Fixture scope rules

- **session**: immutable data, no test mutates it.
- **function** (default): anything tests modify.
- Never widen scope if a test writes to the fixture object in place.

### Qt / GUI tests

- Headless: `QT_QPA_PLATFORM=offscreen` when appropriate.
- One app fixture per session, not per test.
- Avoid `processEvents()` loops unless timing is under test.

## Phase 5 — Implement incrementally

1. Pick one file or one slow cluster from `--durations`.
2. Consolidate **or** optimize — not both in one giant diff when avoidable.
3. Run **targeted** tests for touched paths (see project `testing.mdc` / pre-commit mappings).
4. Re-run `--durations` on affected files to confirm improvement.
5. Repeat until diminishing returns or user scope is met.

**Do not** run the full suite after every tiny edit unless the change is broad (`conftest.py`, core loader, registry).

## Phase 6 — Report

Deliver this summary to the user:

```markdown
## Test suite optimization report

### Baseline
- Full suite: Xs (N tests)

### Changes
- [file] — consolidated M→K tests / session fixture for … / tmp_path instead of assets
- …

### After
- Full suite: Ys (Δ%)
- Slowest remaining: test_name (Zs) — reason — optional follow-up

### Coverage notes
- Behaviors still covered: …
- Intentionally unchanged heavy tests: …
```

## Checklist

```
- [ ] Baseline timings captured
- [ ] Slow tests categorized (I/O, imports, fixtures, UI, assets)
- [ ] Consolidation preserves distinct failure modes
- [ ] Fixture scopes reviewed (no shared mutable state)
- [ ] Targeted pytest green after each batch
- [ ] Final durations compared to baseline
```

## Project-specific hooks (structure_scripts)

When this repo is the workspace:

- Follow `.cursor/rules/testing.mdc` for targeted vs full runs.
- Path → test mappings live in `scripts/pre-commit-pytest.sh`.
- Heavy asset tests: `@pytest.mark.requires_assets` (see `tests/conftest.py`).
- Sprite baker / texture tests: prefer `tmp_path` images; avoid reloading full `BLOCK_REGISTRY` per test.
- UI tests: `tests/test_main_window.py` — keep minimal; mock document where possible.

## Additional reference

- Pytest patterns and anti-patterns: [reference.md](reference.md)
