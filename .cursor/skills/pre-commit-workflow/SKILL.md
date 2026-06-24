---
name: pre-commit-workflow
description: >-
  Fix and pass structure_scripts pre-commit hooks in order (ruff, palette
  validation, targeted pytest). Use when commit fails, pre-commit errors appear,
  preparing to git commit, or fixing ruff E501, validate_palettes, or pytest hook
  failures.
---

# Pre-Commit Workflow

Hooks run **in order** on every commit (see `.pre-commit-config.yaml`):

1. **ruff** — `scripts/pre-commit-ruff.sh`
2. **validate-palettes** — `scripts/pre-commit-validate-palettes.sh`
3. **pytest** — `scripts/pre-commit-pytest.sh`

Fix failures **top to bottom**. Do not skip hooks unless the user explicitly asks.

Pair with [targeted-testing](../targeted-testing/SKILL.md) for pytest selection. Hook failure memory: [reference.md](reference.md) § Failure patterns.

## Before committing (mandatory)

1. Stage intended files: `git add …`
2. **Simulate the pytest hook** on staged paths (not a hand-picked subset):

   ```bash
   scripts/pre-commit-pytest.sh
   ```

   This is the same script the commit hook runs. If it chooses **full suite**, run `.venv/bin/pytest -q` until green. See [targeted-testing](../targeted-testing/SKILL.md) §5–§6 for scope rules and post-fix re-runs.
3. After a test failure fix, re-run `scripts/pre-commit-pytest.sh` (or full suite if that was the scope) — **not** only the one failing file unless the hook listed a single file.
4. Optional after green pytest on **same staged hash**:

   ```bash
   scripts/record-pytest-pass.sh
   ```

   Pre-commit may skip pytest for 30 minutes; ruff and palettes still run.

## Hook 1 — Ruff (fix + format, re-stage)

**Script:** `scripts/pre-commit-ruff.sh`

- Runs on **staged** `*.py` / `*.pyi` only
- `ruff check --fix` then `ruff format`
- **Re-stages** fixed files automatically

| Failure | Fix |
| ------- | --- |
| E501 line too long | Wrap strings/signatures; keep lines ≤ **100** chars (`pyproject.toml`); split long markdown-in-Python |
| B007 unused loop var | Prefix with `_` |
| Import sort | Usually auto-fixed |
| Hook passed but commit still dirty | Hook re-staged files — `git add` any you changed after, or commit again |

Manual fix:

```bash
scripts/ruff-fix    # or: .venv/bin/ruff check --fix . && .venv/bin/ruff format .
```

After manual ruff on staged paths, re-stage and retry commit.

## Hook 2 — Palette / registry integrity

**Script:** `scripts/pre-commit-validate-palettes.sh` → `validate_palettes()`

| Failure pattern | Fix |
| --------------- | --- |
| `unknown token` in palette YAML | Add behavior or fix palette ref |
| `top texture … not found` | Add texture under assets, bake sprite, or skip token in validate (only if render has no `top` key — see `registries/validate.py`) |
| Invalid block entry in terrain palette | Fix `registries/palettes/terrain.yaml` shape |
| Missing catalog id | Run `scripts/generate_catalog.py` after asset update |

Local check:

```bash
.venv/bin/python -c "from registries.validate import validate_palettes; validate_palettes()"
```

Requires `assets/minecraft/textures/block/` with PNGs for strict texture checks; if assets absent, texture checks may no-op.

## Hook 3 — Pytest (targeted by staged paths)

**Script:** `scripts/pre-commit-pytest.sh`

| Output | Meaning |
| ------ | ------- |
| `N file(s) — test_…` | Targeted run — fix failures in those tests |
| `full suite (core or global change detected)` | Staged core files — run full `pytest` or fix until green |
| `full suite (unmapped code changes)` | Staged `.py` not in script map — run full suite or extend script |
| `full suite (N targeted files > 20)` | Too many test files — run full suite |
| `skipped (recent pass for same staged files)` | `record-pytest-pass.sh` worked |
| `skipped (no mapped code changes)` | Docs-only or non-code — OK |

See [targeted-testing/reference.md](../targeted-testing/reference.md) for path→test map. Failure patterns: [reference.md](reference.md) § Failure patterns (`precommit-pytest-scope-mismatch`).

On pytest failure: fix code → rerun `scripts/pre-commit-pytest.sh` (or full suite if hook chose that) → retry commit.

**Commit-issue card:** when a hook fails, `scripts/on_pre_commit_failure.sh` writes a **`commit-issue`** card under `.devtool/features/` with **`## Problem`** and **`## Failed Tests`**. Look for `commit-issue card created: .devtool/features/commit-issue-<hook>-<timestamp>.md` in hook output (cards are gitignored). User asks agent to **review** → agent adds **Root Cause** and **Corrective Action**; user approves → asks to **implement**. Disable capture: `SKIP_COMMIT_ISSUE_CARD=1 git commit …`. No card after failure → grep `precommit-stash-old-hooks` in [reference.md](reference.md) and stage hook infra. See [kanban-commit-issue-cards.mdc](../rules/kanban-commit-issue-cards.mdc).

## Retry commit loop

```text
git add …
git commit -m "…"
  → ruff fails? fix → add → commit again
  → palettes fail? fix registry/palette → commit again
  → pytest fails? fix → targeted pytest → commit again
```

**Do not** `--no-verify` unless user explicitly requests.

## Skip pytest only (still runs ruff + palettes)

```bash
scripts/commit-no-pytest -m "message"
# or
SKIP=pytest git commit -m "message"
```

User should run targeted tests before push. Agent: run targeted tests yourself before using skip.

Alternative: `SKIP_PRECOMMIT_PYTEST=1 git commit …` (pytest script only).

## Run hooks without committing

```bash
pre-commit run --all-files              # everything
pre-commit run ruff-fix-format          # hook 1
pre-commit run validate-palettes        # hook 2
pre-commit run pytest                   # hook 3
```

## Common agent mistakes

| Mistake | Instead |
| ------- | ------- |
| Full `pytest` after one file change | [targeted-testing](../targeted-testing/SKILL.md) |
| `--no-verify` on first failure | Fix the reported hook |
| Re-run same failing test with no edit | Change code or analysis first |
| Amend after failed hook | New commit after fix (see user git rules) |
| Ignore ruff re-stage | Check `git status` after hook 1 |

## Checklist

```
- [ ] Files staged
- [ ] Targeted pytest green (or record-pytest-pass)
- [ ] Commit attempted
- [ ] Ruff issues fixed (line length, unused vars)
- [ ] validate_palettes() green if registry/palette touched
- [ ] Pre-commit pytest green or justified full suite
```

Related: [reference.md](reference.md), [agent-triage](../agent-triage/SKILL.md), [development.md](../../docs/development.md).
