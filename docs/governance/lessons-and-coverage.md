# Lessons and coverage

## Lessons reference index

Committed registry of promoted lessons grouped by feature area (paths + Signatures only — not full card prose).

| Field | Meaning |
| ----- | ------- |
| `version` | Schema version (`1`) |
| `generated_at` | ISO-8601 UTC timestamp from last generator run |
| `areas.<label>.signatures` | Promotion Signatures grep'd from done/archived cards |
| `areas.<label>.done_cards` | Relative paths to cards with `## Lessons captured` |
| `areas.<label>.artifacts` | Governance links (skills, rules, docs) from lesson bullets |

Refresh after **Card Done** lessons capture or before a quarterly governance audit:

```bash
python3 scripts/build_lessons_index.py
python3 scripts/build_lessons_index.py --check   # exit 1 when stale
```

**Agent read order (kanban pre-implementation):** skim the card's area block in
`docs/lessons-index.yaml`, then [agent-triage/reference.md](../../.cursor/skills/agent-triage/reference.md)
§ **Lessons by area**, then `resolve_prior_lessons.py` — open full done cards only when still
ambiguous ([kanban-prior-lessons-gate.mdc](../../.cursor/rules/kanban-prior-lessons-gate.mdc)). **Do not**
broad `grep` / `Glob` on `.devtool/features/done/` or `archived/` for lesson discovery — Signature:
`governance-index-not-grep` ([kanban-markdown/reference.md](../../.cursor/skills/kanban-markdown/reference.md)
§ Index vs folder grep). For
gc5 **forward-feedback questions** (not promoted lessons), use `docs/forward-feedback-index.yaml`
and `resolve_forward_feedback.py --category … --top N` after the lessons index when the task is
backlog/ranking, not prior-lessons citation (Signature: `forward-feedback-index`).

When `.devtool/features/` is absent (CI clone without kanban), the generator skips writing; tests use `tmp_path` fixtures.

Epic `LessonsReferenceIndex` (li0–li3) — index build (this section), structured `artifacts:` on cards, registry pointers, triage routing.

## Lessons Coverage Metric

Measures how effectively lessons from **Done** and **commit-issue** cards flow into durable artifacts and back into new card work via the **prior lessons gate**. Epic `LessonsCoverageMetric` (lc0–lc3).

**Related workflow:**

- [**Card Done** lessons capture](../../.cursor/skills/kanban-markdown/SKILL.md) — `feature` / `bug` / `agent` / `commit-issue` cards; optional ``artifacts:`` tail (schema below)
- [**Prior lessons gate**](../../.cursor/rules/kanban-prior-lessons-gate.mdc) — run before **Decisions** / **Corrective Action** on active cards
- [`resolve_prior_lessons.py`](../../scripts/resolve_prior_lessons.py) — surfaces `done/` + `archived/` lessons, registry pointers, commit-issue overlap; `--audit` delegates to coverage lib
- [**Periodic governance audit**](audit-and-compaction.md#periodic-governance-audit) — quarterly checklist includes `check_lessons_coverage.py` when `done/` exists

**v1 rollout:** lc0 spec → lc1 `check_lessons_coverage.py` → lc2 C2/C3 heuristics → lc3 CI drift. First automation targeted **C1 + C4**; full C2/C3 scoring landed in lc2.

| ID | Name | Formula (summary) |
| -- | ---- | ----------------- |
| C1 | Capture Coverage | done cards with ≥1 resolvable promotion / done cards with `## Lessons captured` |
| C1b | Forward Feedback | label-scoped cards with lessons captured (parent ff optional — fcp3) |
| C2 | Promotion Quality | correctly typed refs / total governance refs (skip cards with zero refs) |
| C3 | Consumption Coverage | surfaced lesson cards / expanded relevant set (`surfaced / relevant`) |
| C4 | Application Coverage | **Per-card (threshold):** active cards with accepted Prior-lessons cite / eligible active cards. **Aggregate (advisory):** cited surfaced lessons / total surfaced lessons on active cards. |

| ID | Inputs (numerator / denominator) |
| -- | -------------------------------- |
| C1 | **Num:** closed cards (`done/` + `archived/`) whose `## Lessons captured` has ≥1 on-disk governance path or Signature row in pre-commit-workflow / agent-self-evaluation reference tables. **Den:** cards with non-empty `## Lessons captured`. |
| C1b | **Num:** closed cards with `labels` in `feature` / `bug` / `agent` / `commit-issue` and non-empty `## Lessons captured` (parent `## Forward-looking feedback` **optional** on new closes — fcp3). Legacy cards may still have parent gc5 blocks; grandfather `completedAt` before lc4c ship date (`2026-06-27`) noted in report detail. **Den:** same label set with non-empty `## Lessons captured`. Signatures: `lessons-coverage-c1b-forward-feedback`, `forward-feedback-capture-policy`. |
| C2 | **Num:** governance refs (from ``artifacts:`` or **Governance** bullets) with correct artifact type. **Den:** total refs on cards that promoted at least one ref (cards with zero refs skipped). |
| C3 | **Num:** done/archived lesson cards returned by `find_done_lessons()` (or `find_done_lessons_strict()`). **Den:** expanded relevance set per active card — epic, feature area, **Label Paths**, optional **Context** links (`--strict` drops epic-only match). |
| C4 | **Per-card (threshold):** **Num:** active cards with Label Paths + plan section, ≥1 surfaced lesson, and ≥1 accepted cite in `**Prior lessons (YYYY-MM-DD):**`. **Den:** same cards with ≥1 surfaced lesson (ignore cards with zero surfaced). **Aggregate (advisory):** **Num:** surfaced lessons cited in Prior-lessons block. **Den:** all surfaced lesson hits on eligible active cards. Signature: `lessons-coverage-c4-per-card-threshold`. |

**Composite:** equal weights — `0.2 × (C1 + C1b + C2 + C3 + C4 per-card)` (N/A sub-metrics count as 100%). Aggregate C4 prints in the audit report for deep citation visibility but does **not** drive the 75% drift gate.

**Interpretation:** 90–100 excellent · 75–89 good · 60–74 at risk · &lt;60 governance failure.

**Audit CLI:**

```bash
python3 scripts/check_lessons_coverage.py              # human report; exit 1 when composite < 75
python3 scripts/check_lessons_coverage.py --json
python3 scripts/check_lessons_coverage.py --card .devtool/features/foo.md   # C3 for one card
python3 scripts/check_lessons_coverage.py --strict   # C3: epic alone does not match
python3 scripts/resolve_prior_lessons.py --audit all # C1+C4 subset or full via shared lib
```

**C1** counts resolvable governance paths (on disk) and Signatures (rows in pre-commit-workflow or agent-self-evaluation reference tables).

**C2 — promotion quality** scores whether promoted artifacts use the correct type:

| Artifact path pattern | Expected type |
| --------------------- | ------------- |
| `.cursor/skills/` | skill |
| `.cursor/rules/*.mdc` | rule |
| `*/reference.md` | reference table |
| `` Signature `foo` `` / `sig:` | row in pre-commit-workflow or agent-self-evaluation reference |
| `docs/` | doc |

When a lesson bullet includes structured `artifacts:` (see schema below), C2 uses typed prefixes; otherwise it falls back to **Governance** link heuristics on the same bullet.

**C3 — consumption coverage** compares `find_done_lessons()` output to an expanded relevance set per active card:

- epic match (unless `--strict`)
- feature area label in card body
- path overlap with **Label Paths**
- optional: **Context** links to `done/*.md` or `archived/*.md`

`--strict` calls `find_done_lessons_strict()` — epic alone does not match; require label or path overlap. Report is `surfaced / relevant` per card; default run aggregates across active cards (`todo` / `in-progress` / `review`).

**C4** scans active cards with **Label Paths** and **Decisions** / **Corrective Action** for `**Prior lessons**` citations vs resolver output. Parser SSOT: `resolve_prior_lessons.py` `PRIOR_LESSONS_RE` — text after `**Prior lessons (YYYY-MM-DD):**` until the next `##` heading (mid-block `**` lines do not truncate). Cites done/archived card stems, drift registry stems, Signature backticks, and governance paths.

**Dual C4 reporting (lc4b):** CLI and drift breakdown print **C4 Application (aggregate)** (strict cited/total surfaced — advisory) and **C4 Application (per-card)** (eligible active cards with ≥1 accepted cite — drives composite and the 75% drift threshold). Per-card pass requires ≥1 accepted citation, not every surfaced lesson cited.

**Scope:** `.devtool/features/done/` and `archived/` are gitignored — CI clones without kanban get N/A denominators; tests use `tmp_path` fixtures. Do not commit `.devtool/`.

**Local vs CI:** `check_lessons_coverage.py` and `check_governance_parity.py` skip lessons-coverage drift when neither `done/` nor `archived/` exists under `.devtool/features/` (clean clones, CI without kanban). Optional local hook: `scripts/pre-commit-lessons-coverage.sh` (not enabled in `.pre-commit-config.yaml` by default — add a `lessons-coverage` hook entry manually to fail commits when composite &lt; 75%).

**Governance drift:** `check_governance_parity.py` invokes the same audit when done data exists; composite &lt; 75% (using **C4 per-card** in the composite slot) emits `Lessons coverage drift alert:` with C1–C4 (+ C1b) breakdown including both aggregate and per-card C4 lines (`warn` for 60–74%, `critical` for &lt; 60%). Spawns a **todo** card `lessons-coverage-drift-YYYY-MM-DD` (epic `LessonsCoverageMetric`, label `agent`) unless `--no-spawn-cards`. Spawn body includes **Prior lessons** stub under **Decisions** (not `_TBD` alone) plus agent review sections.

Implementation: `scripts/check_lessons_coverage.py`, `scripts/lessons_coverage_lib.py`; tests `tests/test_check_lessons_coverage.py`. **Parser SSOT:** card/done parsers (`_parse_frontmatter`, `_lessons_excerpt`, `parse_artifacts_line`, …) live in `resolve_prior_lessons.py`; `lessons_coverage_lib.py` imports them (no duplicate parsers). **Test fixtures:** kanban `tmp_path` tests monkeypatch `FEATURES_DIR` on `resolve_prior_lessons` and `check_lessons_coverage`, plus `REPO_ROOT` on `lessons_coverage_lib` — `build_report` stores card paths via `relative_to(REPO_ROOT)`.

## Feature area lesson pointers (li2)

Optional per-area keys in `docs/feature-areas.yaml`:

| Key | Meaning |
| --- | ------- |
| `lesson_signatures` | Curated promotion Signatures (≤8) — grep targets without opening done cards |
| `lesson_docs` | Developer doc paths (≤5) — highlights from lesson captures |

**Manual curation first:** seed and trim lists when closing cards; keep highlights small, not full index dumps.

**Automation suggests only:** `python3 scripts/build_lessons_index.py --sync-registry` prints proposed `lesson_*` diffs from `docs/lessons-index.yaml` (dry-run). Add `--write` to apply when you accept the proposal.

```bash
python3 scripts/resolve_feature_areas.py --lessons "Render Preview"
python3 scripts/resolve_feature_areas.py --agents-parity "Render Preview"
python3 scripts/resolve_prior_lessons.py "Render Preview" --paths helpers/orbit_face_textures.py
```

**`--agents-parity` (gs3):** prints `agents_skill`, `agents_rules`, `lesson_routing_row`, and whether the `lesson_routing_row` anchor appears in [agent-triage/reference.md](../../.cursor/skills/agent-triage/reference.md) § **Lessons by area** (`lessons_by_area_row: found|missing|n/a`). Use during kanban pre-implementation review alongside `--lessons`. Single area label per invocation is typical.

```bash
pytest tests/test_resolve_feature_areas.py -q -k agents_parity
```

Dual **Feature Area** labels on a card union pointers from each resolved area.

## Lessons captured `artifacts:` schema

Optional **machine-readable tail** on each `## Lessons captured` lesson bullet. When present, `build_lessons_index.py` and `resolve_prior_lessons.py` prefer `artifacts:` over free-form **Governance** link heuristics.

**Per-lesson template:**

```markdown
- **Symptom:** animated furnace front tiles multiple openings in orbit preview.
- **Fix:** load frame 0 via `load_block_texture_image`; golden tests use same helper.
  - artifacts: skill:project-context, rule:testing.mdc#orbit-animated-texture-strip, doc:render-types.md, sig:orbit-animated-texture-strip, test:tests/test_block_texture_load.py
```

| Prefix | Value | Indexed as |
| ------ | ----- | ---------- |
| `skill:` | skill folder name (e.g. `project-context`) or full `.cursor/skills/…/SKILL.md` | skill path under `.cursor/skills/` |
| `rule:` | `filename.mdc` or `filename.mdc#signature` anchor | `.cursor/rules/filename.mdc` (anchor for humans) |
| `doc:` | doc basename or `docs/…` path (`.md`, `.yaml`, `.yml`) | path under `docs/` |
| `sig:` | promotion Signature slug | `areas.<label>.signatures` (not an artifact path) |
| `test:` | pytest file path | `tests/…` path in `areas.<label>.artifacts` |

One `artifacts:` sub-bullet per lesson (comma-separated entries). Cards without `artifacts:` still work — parsers fall back to **Governance** markdown links and inline `` `sig:signature-slug` `` backticks on lesson bullets (Signature: `lessons-index-inline-sig-backtick`).

**`doc:` notes:** Markdown basenames may omit `.md` (`doc:render-types` → `docs/render-types.md`). Registry YAML under `docs/` **must** include the extension (`doc:lessons-index.yaml`, `doc:feature-areas.yaml`) — extensionless registry stems such as `doc:lessons-index` are skipped (Signature: `artifacts-doc-yaml-normalize`). Use `rule:` for `.mdc` files, not `doc:`.

**Overlap with `LessonsCoverageMetric` lc2:** structured `artifacts:` is preferred for C2 promotion-quality scoring; parsers prefer `artifacts:` over **Governance** heuristics when present ([`check_lessons_coverage.py`](../../scripts/check_lessons_coverage.py) — `audit_promotion_quality`).

* [AGENTS.md](../../AGENTS.md) — entry index for Cursor agents
* [Consistency matrix](../../.cursor/skills/agent-triage/reference.md#consistency-matrix) — governance artifact parity lookup
* [Drift alert examples](../../.cursor/skills/agent-triage/reference.md#drift-alert-examples) — six named prefixes for parity warnings (matrix / audit anchors)
* **Surfacing:** governance-edit turns — Context load (self-eval §2b check 5), §6g, handoff `- **Drift alerts:**` — [agent-self-evaluation/SKILL.md](../../.cursor/skills/agent-self-evaluation/SKILL.md) §6g; detection — [agent-triage/SKILL.md](../../.cursor/skills/agent-triage/SKILL.md) § Governance drift detection
* `.cursor/rules/agent-consistency.mdc` — same-turn parity when editing governance skills, rules, or `AGENTS.md`
* Self-eval §6g — [agent-self-evaluation/SKILL.md](../../.cursor/skills/agent-self-evaluation/SKILL.md) — end-of-turn consistency prompts when those paths change
