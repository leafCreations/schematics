# Feature areas and parity

## Governance area schema (gs0)

Optional per-area keys in `docs/feature-areas.yaml` for **mechanical** agent routing and parity checks — so prior-lessons gates and `check_governance_parity.py` do not rely on parsing AGENTS.md markdown tables.

| Key | Type | Purpose |
| --- | ---- | ------- |
| `agents_skill` | string | Primary skill stem (e.g. `ui-change`) — gate step loads `.cursor/skills/{stem}/SKILL.md` |
| `agents_rules` | list | Rule stems under `.cursor/rules/` with optional `#signature` (e.g. `ui-panels.mdc`, `testing.mdc#orbit-animated-texture-strip`) |
| `lesson_routing_row` | string \| null | Anchor label in [agent-triage/reference.md](../../.cursor/skills/agent-triage/reference.md) § **Lessons by area** first column; `null` when `lessons-index.yaml` area block is enough |

**Relationship to lesson pointers and index:**

| Artifact | Role |
| -------- | ---- |
| `lesson_signatures` / `lesson_docs` (li2) | Curated grep/doc highlights per area — manual curation; `--lessons` on `resolve_feature_areas.py` |
| `docs/lessons-index.yaml` | Committed index of promoted Signatures, done cards, artifacts — built by `build_lessons_index.py` |
| `lesson_routing_row` | Links an area to a row in triage § **Lessons by area** for pre-implementation read order |
| `agents_skill` / `agents_rules` | Links an area to load-when-touching skills and scoped rules (`check_area_schema_parity` in `check_governance_parity.py` — gs2) |

All governance keys are **optional** and **backward compatible** — areas without them behave as today until gs1 seeds high-traffic areas.

**Out of scope (gs0–gs3):** editing or generating AGENTS.md **Area → skills & rules** table rows from yaml — **gs4 complete** (below).

**gs4 (complete):** `scripts/sync_agents_area_table.py` — `--check` exits non-zero on drift; `--write` / `--fix` updates the AGENTS area table from yaml `agents_skill` / `agents_rules` for seeded areas. Integrated into `check_governance_parity.py`. Signature: `governance-area-schema-agents-table-sync`.

```bash
python3 scripts/sync_agents_area_table.py --check
python3 scripts/sync_agents_area_table.py --write   # refresh AGENTS table only
pytest tests/test_check_governance_parity.py tests/test_sync_agents_area_table.py -q -k area_table
```

**gs3 (complete):** `--agents-parity` on `resolve_feature_areas.py`; pytest `agents_parity` tests; pre-commit maps `feature-areas.yaml` / parity script changes to schema tests.

**Registry path compare (schema-internal):** `check_registry_parity` compares **Agent Workflow** `paths` with skill/rule links extracted from AGENTS area rows. Paths validated elsewhere are excluded via `is_schema_internal_registry_path` / `filter_registry_compare_paths`: `docs/lessons-index.yaml`, `docs/forward-feedback-index.yaml`, `scripts/build_lessons_index.py`, `scripts/build_forward_feedback_index.py`, `scripts/resolve_*.py`, and **Lessons Coverage Metric** tooling (`scripts/check_lessons_coverage.py`, `scripts/lessons_coverage_lib.py`, `scripts/pre-commit-lessons-coverage.sh`, `tests/test_check_lessons_coverage.py`). Do not add script paths to AGENTS area table columns — register them under **Agent Workflow** `paths` + `handlers:` instead.

**gs1 seed areas (complete):** Render Preview, Agent Workflow, Properties Panel, Feature Area Registry, Palette Registry — `agents_skill`, `agents_rules`, `lesson_routing_row` in `docs/feature-areas.yaml`.

Epic `GovernanceAreaSchema` (gs0–gs3) — **complete**. Epic `AgentsTableSync` (gs4) — **complete** — AGENTS area table sync from yaml.

## On-demand parity check

Ad-hoc drift detection between audits (uses phase 1 alert prefixes — paste output into Context load / handoff):

```bash
python3 scripts/check_governance_parity.py
python3 scripts/check_governance_parity.py --line-counts   # gc0 baseline sizes (exit 0)
python3 scripts/check_governance_parity.py --forward-feedback-audit --no-spawn-cards
python3 scripts/check_governance_parity.py --forward-feedback-stale --stale-days 30 --no-spawn-cards
```

Options: `--quiet` (exit code only). `--plain` omits `[severity]` prefixes. **`--no-spawn-cards`** skips kanban card creation. By default, consolidated drift issues spawn **todo** kanban cards under `.devtool/features/` (epic `GovernanceDriftFix` — **`GovernanceDriftAlert` closed**; priority from severity) with **## Alert**, **## Feature Areas**, **## Product Paths**, **Product Methods**, **Tests**, **Docs**, **Decisions**, and **Acceptance Criteria** — duplicates skipped when the same consolidation group already has an open card. **Lessons coverage** drift (when `.devtool/features/done/` or `archived/` exists) uses epic `LessonsCoverageMetric`, label `agent`, and card id `lessons-coverage-drift-YYYY-MM-DD`. Registry checks include optional `handlers:` symbols (malformed lines, duplicates across areas, kanban **Product Methods** missing from yaml; legacy **Label Methods** headings still read).

### Registry drift spawn consolidation

`consolidate_drift_issues_for_spawn` merges alerts before card creation — Signature:
`governance-drift-spawn-consolidate-by-root-cause` (extends
`governance-drift-spawn-consolidate-by-source-card` for kanban Product Methods only):

| Root cause | Group key | One card lists |
| ---------- | --------- | -------------- |
| Missing `lesson_signatures` routing/index | `lesson-signatures:{Area}` | All signatures for that feature area |
| Agent Workflow paths vs AGENTS table | `schema-internal-agents-paths` | All yaml paths needing `_SCHEMA_INTERNAL_PATHS` |
| Duplicate `handlers:` across areas | `handler-duplicates` | All handler symbols + area pairs |
| Kanban Product Methods missing from yaml | `registry-label-methods:{card}` | All symbols for one source kanban card |

Card ids hash the **group key** (stable when alert text shrinks as fixes land). Re-runs dedupe via
`consolidation_group_marker` on open cards.

**`--forward-feedback-audit` (gc7 gel2 — advisory):** scans `done/` and `archived/` cards with
`labels` in `feature` / `bug` / `agent` / `commit-issue`, lessons captured, and `completedAt` on or
after lc4c ship date (`2026-06-27`). Reports missing gc5 forward-feedback fields (Impact Scope,
References, Mitigation when category risk ≥ 4, six category sections). **Exit 0 always** — does not
spawn drift cards or fail pre-commit. Complements **C1b** (`check_lessons_coverage.py` — presence of
`## Forward-looking feedback`); this flag audits **field completeness** on post-grandfather cards.
Signature: `governance-gc7-forward-feedback-audit`. Epic audit step 5 (gel0) may run this after
`--line-counts` on governance epics. **ff3 optional:** `--forward-feedback-stale` on
`ForwardFeedbackRegistry` epic close — backlog depth vs gc7 card-field gaps (see Forward feedback
index § Open backlog metrics).
