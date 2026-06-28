# Kanban workflow

## Kanban card scope (Product / Tests / Docs)

Epic **`KanbanCardScope`** (ks0–ks3 **archived 2026-06-28**). Active kanban templates split scope:

| Section | Owner | Purpose |
| ------- | ----- | ------- |
| **Feature Areas** / story / **Verify** | **User** | Product labels; optional behavior AC draft; manual app checks |
| **Product Paths** / **Product Methods** | **Agent** | Product code paths and symbols (no `tests/` in Product Paths) |
| **Tests** | **Agent** | **Files**, **Methods**, **Verify (agent)** — `scripts/pre-commit-pytest.sh` authoritative |
| **Docs** | **Agent** | Doc paths + § hints; pair with [docs-maintenance](../../.cursor/skills/docs-maintenance/SKILL.md) before Review |
| **Acceptance Criteria** | **Agent** (complete) | **Behavior only** — no pytest paths or `test_*` names |

**Legacy:** `done/` / `archived/` cards may keep **Label Paths** / **Label Methods** — parsers read as Product (**ks1**). Rules/skills/AGENTS use **Product** on active cards (**ks2**). Signature: `kanban-card-scope-schema`.

**Parser aliases:** `extract_label_paths` merges **Product Paths**, legacy **Label Paths**, and **Tests → Files**; registry drift uses **Product Methods** in alert text.

**Tests verify gate (ks3):** draft card **Tests → Files** from Product Paths with
`python3 scripts/resolve_card_tests.py --from-card CARD.md --files-only` (simulates
`scripts/pre-commit-pytest.sh` via `PRE_COMMIT_PYTEST_LIST_ONLY=1`). Before **Review**, stage intended
paths and run `scripts/agent-commit-ready.sh` (ruff → palettes → pytest) or hook scripts individually.
**Tests → Verify (agent)** must cite `scripts/pre-commit-pytest.sh`. Signatures:
`precommit-pytest-scope-mismatch`, `2d-stair-riser-runtime-cache-test`.

## Cursor mode gates (Plan / Inquire / verbs)

Epic **`KanbanCursorModeGates`** (cm0–cm3 **complete 2026-06-29**). Schema, scoped rules, and
Classify SSOT shipped; fingerprint `fe1e226a461904d1`. Canonical matrix:
[kanban-markdown/reference.md § Cursor mode gates](../../.cursor/skills/kanban-markdown/reference.md#cursor-mode-gates-plan--inquire--verbs);
parity: `check_classify_parity`, `check_kanban_rule_globs` — Signatures: `kanban-cursor-mode-gates`,
`governance-compact-classify-ssot`, `governance-compact-kanban-rule-globs`. Epic close: gel0 audit on
cm0 anchor → [../epics-closed.yaml](../epics-closed.yaml).

## User prompts (agent workflow)

Canonical verb/mode matrix: [kanban-markdown/reference.md § Cursor mode gates](../../.cursor/skills/kanban-markdown/reference.md#cursor-mode-gates-plan--inquire--verbs) — do not duplicate here.


Rare same-turn: `review and update`, `plan and update`. Legacy `Kanban: answer inquiry on …` → use
**Inquire** then **update**. Full matrix: [kanban-markdown/reference.md § Cursor mode gates](../../.cursor/skills/kanban-markdown/reference.md#cursor-mode-gates-plan--inquire--verbs).

- `python scripts/resolve_feature_areas.py "<label>"` — paths; `--handlers` for registry entry-point symbols; `--lessons` for curated `lesson_signatures` / `lesson_docs`
- `python3 scripts/resolve_card_tests.py PATH…` or `--from-card CARD.md` — hook test selection for Product Paths
- `python3 scripts/resolve_prior_lessons.py --epic "<Epic>" "<Feature Area>" --paths …` — done/archived-card lessons + open commit-issue overlap + **Registry lesson pointers** when present
- `python3 scripts/check_lessons_coverage.py` — Lessons Coverage Metric audit (C1–C4); `--card`, `--strict`, `--json`
- `python3 scripts/build_lessons_index.py` — regenerate `docs/lessons-index.yaml` from Card Done captures; `--check` for stale index; `--dry-run` to stdout; `--sync-registry` proposes `lesson_*` keys in `docs/feature-areas.yaml` (dry-run; add `--write` to apply)
