# Kanban Markdown — Reference

**Lifecycle and gates:** [SKILL.md](SKILL.md). **Card-type constraints:** scoped `kanban-*.mdc` rules —
do not duplicate who-writes-what tables here; link to the matching rule. Signature:
`governance-compact-kanban-split` (gc1 — SKILL ≤ ~400 lines lifecycle; this file on demand).

Load this file for templates, section-order examples, file format, and audit checklist detail.

## Kanban card scope (Product / Tests / Docs)

Epic **`KanbanCardScope`** (ks0–ks3). Active templates use **Product Paths**, **Product Methods**,
**Tests**, and **Docs** instead of mixing product paths, pytest commands, and doc paths under
**Label** sections or **Acceptance Criteria**. Signature: `kanban-card-scope-schema`.

### Terminology map (Label → Product)

| Legacy (valid on open cards until ks2) | New (active templates) |
| -------------------------------------- | ---------------------- |
| **`## Label Paths`** | **`## Product Paths`** |
| **`## Label Methods`** | **`## Product Methods`** |

Parsers accept **both** heading pairs until **ks1** ships ([ks1 card](
../../.devtool/features/agent-kanban-card-scope-ks1-parsers-spawn-2026-06-27.md)).
Cards under **`done/`** and **`archived/`** may keep **Label** headings — **no** mandatory
retroactive rename.

### Section ownership

| Section | Who | Content |
| ------- | --- | ------- |
| **Feature Areas** / **Feature Area** | User | Optional product labels only |
| **Acceptance Criteria** | User (draft) / Agent (complete) | **Behavior / intent only** — no pytest commands, no `tests/` paths, no `test_*` names |
| **Product Paths** | Agent | Product code paths — **no** `tests/` |
| **Product Methods** | Agent | `path` — `symbol` bullets for symbols this card will change |
| **Tests** | Agent | **Files**, **Methods**, **Verify (agent)** — pytest scope lives here |
| **Docs** | Agent | Doc paths + optional § hints; align with `docs:` on resolved Feature Areas |
| **Decisions** / **Corrective Action** | Agent | Concrete plan before `in-progress` |
| **Verify** | User | Manual app checks only — not agent pytest |

**Lifecycle:** inquiry/review spawn may leave Product / Tests / Docs as `_TBD_`; all three must be
accurate before **in-progress → review** (mandatory at implementation gates).

**Section glossary (ccp1):** [reference-glossary.md](reference-glossary.md) — Signature:
`kanban-card-section-glossary`. Do not duplicate glossary tables in scoped `kanban-*-cards.mdc`.

### Acceptance Criteria (behavior only)

**Do not** put pytest commands, test file paths, or `test_*` function names in AC — use **Tests**.

```markdown
## Acceptance Criteria

- [ ] Zoom resets when switching back to the Viewer tab
- [ ] Stale preview PNGs re-render after save
```

**Avoid:**

```markdown
- [ ] `pytest tests/test_preview_panel.py -q` passes
- [ ] Add `test_preview_panel_zoom_scales_pixmap`
```

**Floating Camera keyboard:** when Feature Areas include **`Floating Camera`**, add a hold-to-fly AC
bullet — see [kanban-feature-cards.mdc](../../rules/kanban-feature-cards.mdc) § Floating Camera
keyboard movement; Signature: `floating-camera-fc0-hold-fly`.

### Product Paths and Product Methods

Repo-relative paths in **`## Product Paths`**; symbols in **`## Product Methods`** — card body, not
frontmatter. Resolve Feature Areas via [docs/feature-areas.yaml](../../docs/feature-areas.yaml);
**Product Paths** must not list `tests/` (those belong under **Tests → Files**).

#### Example (agent after card review)

```markdown
## Product Paths

- `ui/main_window.py`
- `ui/reload.py`

## Product Methods

- `ui/main_window.py` — `MainWindow._on_open_structure`, `MainWindow._restart_editor_for_structure`
- `ui/reload.py` — `open_structure_in_editor_process`
```

#### User creates card (example)

```markdown
## Feature Areas

- `Render Tab`
- `Render Preview`
- `Render Selection`
```

#### Agent after review (example)

```markdown
## Product Paths

- `ui/widgets/preview_panel.py`
- `ui/main_window.py`

## Product Methods

- `ui/widgets/preview_panel.py` — `PreviewPanel._set_zoom_factor`, `PreviewPanel.reset_zoom_to_default`
- `ui/main_window.py` — `MainWindow._on_tab_changed`
```

**Product Methods rules:** symbols this card will change only; ≤8 per file, ≤20 total; open
**Product Methods** (or legacy **Label Methods**) first during implementation.

### Tests

Agent-owned pytest scope. Split from AC so commit-time hook coverage is explicit
(Signature: `precommit-pytest-scope-mismatch`).

```markdown
## Tests

### Files

- `tests/test_preview_panel.py`

### Methods

- `tests/test_preview_panel.py` — `test_preview_panel_zoom_scales_pixmap`

### Verify (agent)

`scripts/pre-commit-pytest.sh` on staged paths (authoritative scope — maps staged files to pytest
via [scripts/pre-commit-pytest.sh](../../scripts/pre-commit-pytest.sh)). Targeted manual runs:
`pytest tests/test_preview_panel.py -q` when iterating.
```

| Subsection | Content |
| ---------- | ------- |
| **Files** | Test modules under `tests/` |
| **Methods** | `path` — `test_*` or `-k` filter notes |
| **Verify (agent)** | Pre-commit hook script and/or targeted pytest — **not** user **Verify** |

### Docs

Agent-owned documentation touch list — product code paths belong in **Product Paths**, not here
([docs-maintenance](../docs-maintenance/SKILL.md) change → doc map).

```markdown
## Docs

- `docs/ui.md` — Viewer tab, preview stale behavior
- `docs/feature-areas.yaml` — `Render Preview` `handlers:` when registry changed
```

Seed **Docs** from `docs:` keys on each resolved Feature Area in [docs/feature-areas.yaml](../../docs/feature-areas.yaml).
Add § hints when a specific section must change (e.g. `docs/ui.md` — Viewer tab).

### Feature card section order

1. `# Title` + user story
2. `## Acceptance Criteria` (behavior only)
3. `## Out of Scope` (optional)
4. `## Feature Areas` (user)
5. `## Product Paths` (agent)
6. `## Product Methods` (agent)
7. `## Tests` (agent)
8. `## Docs` (agent)
9. `## Decisions` (agent)
10. `## Verify` (optional — user manual app checks)
11. `## QA Review` (user, during review)

### Picking up a To Do card

1. Read **Feature Areas**; resolve via [docs/feature-areas.yaml](../../docs/feature-areas.yaml)
2. Write **Product Paths** + **Product Methods** + **Tests** + **Docs** before `in-progress`
3. Jump to **Product Methods** symbols first; grep for gaps
4. Map **Tests → Files** via [targeted-testing](../targeted-testing/SKILL.md) and
   `scripts/pre-commit-pytest.sh`
5. Missing area context → [repo-map](../repo-map/SKILL.md)

### Legacy: Label Paths and Label Methods

Until **ks2** governance rollout, **Label Paths** / **Label Methods** on open cards are equivalent
to **Product** sections (same semantics; tests/docs were often mixed into Label — migrate on edit).

```markdown
## Label Paths

- `ui/widgets/preview_panel.py`
- `tests/test_preview_panel.py`

## Label Methods

- `ui/widgets/preview_panel.py` — `PreviewPanel._set_zoom_factor`
- `tests/test_preview_panel.py` — `test_preview_panel_zoom_scales_pixmap`
```

## Kanban card sections (glossary)

Full **row schema**, **glossary tables**, **anti-patterns**, and **label matrix:**
[reference-glossary.md](reference-glossary.md) — Signature: `kanban-card-section-glossary`,
`governance-thin-kanban-reference` (krt3 split).

## Cursor mode gates (Plan / Inquire / verbs)

Signature: `kanban-cursor-mode-gates`. Canonical matrix:
[kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2;
[kanban-plan-cards.mdc](../../rules/kanban-plan-cards.mdc);
[kanban-inquiry-cards.mdc](../../rules/kanban-inquiry-cards.mdc).

| Prompt | Cursor mode | Card file edits |
| ------ | ----------- | --------------- |
| `Plan @card` | Plan | Chat only until `plan approved` / `update` |
| `Inquire @card` | Ask | Chat only until `update` |
| `implement` / `update` / `spawn` / `Done` | Agent | Per scoped `kanban-*-cards.mdc` |

Rare compounds (`review and update`, `plan and update`): [reference-glossary.md § Anti-patterns](reference-glossary.md#anti-patterns).

## Card types (templates)

Who-writes-what and workflow: scoped `kanban-*-cards.mdc` + [SKILL.md](SKILL.md). **Do not** duplicate
tables here (Signature: `governance-compact-kanban-split`).

| Label | Rule | Agent plan section |
| ----- | ---- | ------------------ |
| `feature` | [kanban-feature-cards.mdc](../../rules/kanban-feature-cards.mdc) | **Decisions** |
| `bug` | [kanban-bug-cards.mdc](../../rules/kanban-bug-cards.mdc) | **Corrective Action** |
| `agent` | [kanban-agent-cards.mdc](../../rules/kanban-agent-cards.mdc) | **Decisions** |
| `commit-issue` | [kanban-commit-issue-cards.mdc](../../rules/kanban-commit-issue-cards.mdc) | **Corrective Action** |
| `inquiry` | [kanban-inquiry-cards.mdc](../../rules/kanban-inquiry-cards.mdc) | **Response** (after `update`) |
| `plan` | [kanban-plan-cards.mdc](../../rules/kanban-plan-cards.mdc) | **Recommendation** (after approval) |
| `feedback` | [kanban-feedback-cards.mdc](../../rules/kanban-feedback-cards.mdc) | **Question** + **Risk assessment** |

**Feedback (fcp1):** spawn + risk rubric — [§ Forward-feedback capture cadence](#forward-feedback-capture-cadence);
example schema in [reference-glossary.md](reference-glossary.md) or archived fcp0 anchor.

## Spawn, epics, and drift

- **Spawn from inquiry/plan:** [SKILL.md § Spawn from inquiry](SKILL.md#spawn-from-inquiry) — `epic` +
  `order`; review-ready Product / Tests / Docs / Decisions (or CA for bugs).
- **Drift spawn skeleton:** parity spawns need full section placeholders (`_TBD_`) — Signatures:
  `lessons-coverage-ci-drift`, `governance-drift-spawn-consolidate-by-root-cause`; see
  [docs/governance/feature-areas-parity.md](../../docs/governance/feature-areas-parity.md).
- **Epic anchor:** `## Epic cards` manifest; **`## Epic coordination`** in-flight only (never ff index) —
  Signature: `epic-coordination-not-forward-feedback`.
- **gel0 / gel3 / gel4:** `resolve_epic_cards.py`, `resolve_archive_group.py`, `docs/epics-closed.yaml`;
  chat **`### Epic summary`** / **`### Initiative summary`** —
  [docs/governance/kanban-workflow.md](../../docs/governance/kanban-workflow.md).
- **Closed epic spawn tables:** `docs/epics-closed.yaml` only — Signature: `governance-thin-kanban-reference`.

## Prior lessons gate

Canonical procedure: [SKILL.md § Prior lessons gate](SKILL.md#prior-lessons-gate).
Rule: [kanban-prior-lessons-gate.mdc](../../rules/kanban-prior-lessons-gate.mdc).

### Index vs folder grep (acb4)

Signature: `governance-index-not-grep`. Yaml + `resolve_prior_lessons.py` first — no broad
`done/` / `archived/` grep. Forward-feedback ranking: `forward-feedback-index.yaml` +
`resolve_forward_feedback.py` (not prior-lessons). Resolver args: `--epic`, Feature Area labels,
`--paths` from Product Paths. Full ladder: [SKILL.md § Prior lessons gate](SKILL.md#prior-lessons-gate-pre-implementation).

## Verify, Decisions, AC, QA Review, QA fixes

**Verify:** agent `scripts/pre-commit-pytest.sh` before Review; user **`## Verify`** = manual app only.
**Decisions** (feature/agent) / **Corrective Action** (bug/commit-issue): concrete before `in-progress`.
**AC:** behavior-only `- [x]` before Review — no pytest in AC. **QA Review:** user checklist; agent
implements + `**QA follow-up (YYYY-MM-DD):**` under Decisions/CA — [kanban-review-qa.mdc](../../rules/kanban-review-qa.mdc);
scope refresh table in [SKILL.md § User-reported QA fixes](SKILL.md#user-reported-qa-fixes).

## QA-complete → Card Done (trigger table)

Signature: `card-done-agent-move-qa-complete`. When the user signal matches **and** a kanban card is
named (path, id, or `@.devtool/features/…`), treat as **Agent** mode — move + Card Done **same turn**
(`feature` / `bug` / `agent` / `commit-issue` only).

| User signal (examples) | Agent mode? | Action |
| ---------------------- | ----------- | ------ |
| `Done`, `mark … Done`, `close the card` (card named) | **Yes** | Move → `done/` + § Card Done |
| `QA complete`, `QA approved`, `QA Approved`, `QA accepted`, `QA Accepted`, `Review passed`, `QA-complete` | **Yes** | Same (Review finished — not a QA *fix* request; case-insensitive) |
| Bare `@path` or `review @card` only | **No** | Ask-only — [kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2 |
| `review and update`, `implement`, `update … card` | **Yes** | Prior agent verbs — not Card Done unless also Done signal |
| Inquiry `Done` | **Yes** (move only) | `done/` — **no** Lessons captured / forward feedback |

### Disambiguation (card unnamed)

Signature: `card-done-disambiguate-multi-review` (extends gc8 `card-done-agent-move-qa-complete`).
When the user signal matches Card Done but **does not** name a card (`@path`, id slug, or
unambiguous prose), count active cards with `status: review` under `.devtool/features/` only — not
`done/`, `archived/`, Backlog, or `in-progress`.

| Cards in **review** | User: Done / QA complete (no card named) | Agent |
| --- | --- | --- |
| **0** | Done signal | **Stop** — nothing to close; ask which card |
| **1** | Done signal | **May proceed** — infer the sole review card |
| **≥ 2** | Done signal | **Hard stop** — list review candidate paths; require `@.devtool/features/….md` or slug; **do not guess** |

Board scan before Card Done when card unnamed:

```bash
rg 'status: "review"' .devtool/features/*.md
```

Apply to all trigger phrases above (`Done`, `QA complete`, `QA Approved`, `Review passed`,
`close the card`, …). **Does not** change inquiry/plan Done (move-only, no lessons). No thread-context
override when count ≥ 2 (user decision, 2026-06-29).

**Same turn (mandatory for labeled cards):**

1. Frontmatter: `status: done`, `completedAt`, bump `modified`
2. Move `.devtool/features/{id}.md` → `.devtool/features/done/{id}.md`
3. Append `## Lessons captured` on `done/` path; spawn **`feedback`** and/or legacy parent
   `## Forward-looking feedback` per § Forward-feedback capture cadence
4. `python3 scripts/build_lessons_index.py` when lessons ran
5. `python3 scripts/build_forward_feedback_index.py` when lessons ran — Signature:
   `forward-feedback-card-done-ingest`; advisory exact-question dedup → `duplicate_of` in yaml
   + stderr; surface lines in chat as **`### Forward feedback dedup`** (non-blocking)
6. `### Top forward feedback` in chat (agent-self-evaluation §7)

**Not Card Done:** user reports Review bugs → stay in **review** with `**QA follow-up**` ([kanban-review-qa.mdc](../../rules/kanban-review-qa.mdc)).

**Maintain (gc8):** new Done-signal phrases → this table + `kanban-card-gates.mdc` §2 Card Done row
only — do not duplicate full trigger lists in scoped `kanban-*-cards.mdc`. Classify fingerprint bump
only when `agent-triage/reference.md` § Classify **rows** change, not trigger-table edits alone.
**Maintain (gc9):** disambiguation rule changes → this § Disambiguation subsection only; bump
`REFERENCE_CLASSIFY_FINGERPRINT` when Classify row changes — Signature:
`card-done-disambiguate-multi-review`.
`` `sig:card-done-agent-move-qa-complete` ``

## Card Done — lessons learned capture

Canonical summary: [SKILL.md § Card Done](SKILL.md#card-done--lessons-learned-capture).

### Artifact update table

Skill + scoped rule + `docs/` / registry; cite **Signature** in rules. Card Done ff: §
[Forward-feedback capture cadence](#forward-feedback-capture-cadence). Index rebuild:
`build_lessons_index.py` then `build_forward_feedback_index.py` — Signature:
`forward-feedback-card-done-ingest`. C4 / prior-lessons / drift / gel0 rows:
[SKILL.md § Card Done](SKILL.md#card-done--lessons-learned-capture).

### Lessons captured example

```markdown
## Lessons captured (2026-06-27)

- **Symptom:** …
- **Fix:** …
  - artifacts: skill:ui-change, rule:testing.mdc#orbit-animated-texture-strip, sig:orbit-animated-texture-strip
```

Prefixes: `skill:`, `rule:`, `doc:`, `sig:`, `test:`. Registry yaml: `doc:lessons-index.yaml` (explicit extension). Inline `` `sig:slug` `` on lesson bullets is indexed by `build_lessons_index.py` — Signature: `lessons-index-inline-sig-backtick`.

### Forward-looking feedback cadence

**New Card Done closes:** § [Forward-feedback capture cadence](#forward-feedback-capture-cadence)
(fcp2 SSOT) — lessons always; spawn **`feedback`** when risk **≥ 3**; **no** mandatory parent
six-category ff. Signatures: `forward-feedback-capture-policy`, `card-done-forward-feedback-cadence`.

**Legacy parent gc5** — archived `done/` cards and index ingest only. Multi-card epic **phase
members** (`epic:` + anchor **`## Epic cards`** ≥2 rows; card ≠ anchor) skip mandatory parent ff;
optional `Forward feedback: deferred to epic {Name}` under **Lessons captured**. In-flight notes →
anchor **`## Epic coordination`** — never index ingest (Signature:
`epic-coordination-not-forward-feedback`). **Scoped Card Done bullets:**
[kanban-feature-cards.mdc](../../rules/kanban-feature-cards.mdc),
[kanban-bug-cards.mdc](../../rules/kanban-bug-cards.mdc),
[kanban-agent-cards.mdc](../../rules/kanban-agent-cards.mdc),
[kanban-commit-issue-cards.mdc](../../rules/kanban-commit-issue-cards.mdc),
[kanban-review-qa.mdc](../../rules/kanban-review-qa.mdc).

### Forward-looking feedback (legacy gc5)

Parent **`## Forward-looking feedback (YYYY-MM-DD)`** on **`feature` / `bug` / `agent` /
`commit-issue`** `done/` cards — **not** on new closes (use **`feedback`** spawns). Field SSOT: §
[Risk assessment rubric](#risk-assessment-rubric). Six categories when present: governance, skill,
rule, codebase, prompt pattern, routing. **Top-3 chat:** risk **≥ 3** only —
[agent-self-evaluation/SKILL.md](../agent-self-evaluation/SKILL.md) §7. Signature:
`card-done-forward-feedback`.

```markdown
## Forward-looking feedback (YYYY-MM-DD)

### Governance
- **Question:** … **Risk Level:** 4 | **Priority:** High | **Importance:** Primary
  **Impact Scope:** system-wide **References:** `check_governance_parity.py`, sig:governance-compact-baseline
  **Mitigation:** … **Detail:** …
```

## Forward-feedback capture cadence

Parent Card Done gate on **feature** / **bug** / **agent** / **commit-issue** — replaces mandatory
parent six-category ff on **new** closes. Signatures: `forward-feedback-capture-policy`,
`card-done-feedback-spawn`. Legacy parent blocks remain in index for archived cards. Policy decisions:
archived fcp0 anchor (`docs/epics-closed.yaml`).

| Card kind | Parent `## Forward-looking feedback`? | Spawn **`feedback`**? | Lessons on Card Done? | Top-3 chat |
| --------- | ------------------------------------- | --------------------- | --------------------- | ---------- |
| **One-off** feature / bug / agent | **No** | When honest risk **≥ 3**; **Risk 5** mandatory spawn | Yes | Risk **≥ 3** only; omit when none |
| **Multi-card epic phase member** | **No** | Same risk gate | Yes (unless anchor batch defer) | Same |
| **Epic anchor at gel0** | **No** synthesis | Consolidate existing open **`feedback`** / index rows | Yes | Existing high-risk only |
| **`commit-issue`** | **No** | Optional when hook implies durable question | Yes | Same |
| **`feedback`** card Done | — | — | **No** | — |

**Parent close steps:**

1. Capture **lessons** always.
2. Score open questions — spawn **`feedback`** todos when risk **≥ 3**; **Risk 5** → mandatory spawn
   same turn (Option A).
3. Append **`## Spawned follow-up cards`** on parent with `feedback` paths (order, label, status).
4. Rebuild index when **`feedback`** spawned or legacy parent ff present; link `` `ff-*` `` on child
   **Context** — Signature: `forward-feedback-card-done-ingest`.
5. **Do not** write parent six-category **`## Forward-looking feedback`** to satisfy Card Done.

**Index SSOT:** **`feedback`** cards primary ingest (fcp2); parent gc5 deprecated for new closes.

## Risk assessment rubric

Shared ranking for **`feedback`** cards, legacy parent gc5 items, and top-3 chat. Signature:
`forward-feedback-risk-rubric`.

| Field | Required | Notes |
| ----- | -------- | ----- |
| **Risk Level** | yes | 1 (Low) – 5 (Critical) |
| **Priority** | yes | 1–2 Low; 3 Medium; 4–5 High (derived from risk) |
| **Impact Scope** | yes | **local**, **multi-card**, or **system-wide** |
| **References** | yes | Rules, skills, signatures, scripts, governance paths; optional `ff-*` |
| **Mitigation** | max-tier only | Concrete step for **every** item at the card's highest risk level |
| **Detail** | risk ≥ 3 | Failure-mode context |
| **Importance** | when tied | **Primary** / **Secondary** / **Tertiary** when ≥2 items share max risk |

**Spawn gate (parent Card Done):** risk 1–2 no spawn (top-3 may include when sole items); 3–4 spawn
**`feedback`** when user attention needed; 5 mandatory **`feedback`** spawn same turn — Option A.

**Top-3 chat:** **`### Top forward feedback`** for risk **≥ 3** only; omit when none spawned and no
legacy parent ff written. **Ranking** (Primary / Secondary / top-3 backfill): Impact Scope
(system-wide > multi-card > local) → category (Governance > Routing > Rule > Skill > Codebase >
Prompt pattern) → failure-mode severity.

**Category (index ingest):** derive gc5 **category** from **References** / Feature Area — not six
`###` headings on parent.

## File format

```markdown
---
id: "my-feature-2026-02-20"
status: "todo"
priority: "medium"
assignee: null
dueDate: null
created: "2026-02-20T10:00:00.000Z"
modified: "2026-02-20T10:00:00.000Z"
completedAt: null
labels: ["feature"]
order: "a0"
---

# My Feature
```

**Serialization:**

- String fields: `"double-quoted"`
- Nullable: bare `null`
- `labels`: inline JSON array on one line — `["feature"]`, `["bug"]`, `["inquiry"]`, `["agent"]`, `["commit-issue"]`
- Field order: `id`, `status`, `priority`, `assignee`, `dueDate`, `created`, `modified`, `completedAt`, `labels`, `order`
- Optional `epic` between `assignee` and `dueDate` on existing cards
- Optional `archiveGroup` after `epic` — cross-epic initiative; batch archive per § Archive group

### Fractional index ordering

- Empty column → `"a0"`
- Append → increment: `"a0"` → `"a1"` … `"a9"` → `"aA"` (base-62)
- Multi-epic governance queue: contiguous `a0`…`a9` in To Do; phase ids in **Context** only

### Creating features

**Do not create in Backlog** unless user asks.

1. Default column: **todo**
2. **ID:** lowercase title → hyphens → `-YYYY-MM-DD`
3. **Body** by type (see card-type sections above)
4. **Done on create:** set `completedAt`, write under `done/`

### Updating / moving

- Always bump `modified`; never change `id` or `created`
- Agent `in-progress` → `review`: pytests, registry, docs, AC `[x]`
- Agent `review` → `done`: on QA-complete signal — frontmatter, move to `done/`, Card Done same turn
- Inquiry `done`: move only — no Card Done sections

## Periodic AGENTS.md governance audit

**Cadence:** quarterly or after large governance epic. Complements [agent-consistency.mdc](../../rules/agent-consistency.mdc).

**Template:** `python3 scripts/create_governance_audit_card.py`

### Who does what

| Step | Who |
| ---- | --- |
| Create todo audit card | User (`create_governance_audit_card.py`) |
| Compare artifacts → **Audit findings** | Agent (read-only) |
| Spawn fix cards | User assigns |
| Move audit → done | User |

### Audit checklist

- [ ] **Routing:** AGENTS Every turn ↔ agent-triage §1/§1b ↔ agent-routing.mdc
- [ ] **Classify:** reference § Classify canonical; AGENTS ≤5-row summary; triage §1 pointer — Signature: `governance-compact-classify-ssot`
- [ ] **Card types:** AGENTS card types ↔ each `kanban-*.mdc` ↔ kanban-markdown SKILL + reference
- [ ] **Handoff:** AGENTS End handoff ↔ agent-self-evaluation §7 ↔ agent-self-evaluation.mdc
- [ ] **Area table:** AGENTS area → skills & rules ↔ Agent Workflow yaml skills
- [ ] **Failure patterns:** Signatures in rules exist in reference tables; Consistency matrix accurate
- [ ] **Docs:** `docs/governance/` handbook ↔ AGENTS + consistency links — Signature: `docs-governance-split`
- [ ] **Lessons coverage:** `check_lessons_coverage.py` when done/ exists; parity script `Lessons coverage drift alert:` matches composite &lt; 75%
- [ ] **Kanban cards:** Feature Areas cards have Product + Tests + Docs (or legacy Label) before `in-progress`

**Output:** drift bullets under **## Audit findings** — do not silently fix during audit turn.

## Docs governance layout

Epic **`DocsGovernanceSplit`** (dg0–dg3) — **closed 2026-06-27** (all phases archived). Signature:
`docs-governance-split`.

**SSOT:** [docs/governance/overview.md](../../docs/governance/overview.md) (handbook hub + audience
table). Product setup stays in [docs/development.md](../../docs/development.md). Do not restore dg1
migration tables here — pointer-first (gc1 / dg2 pattern).

**Verify:** `python3 scripts/check_governance_parity.py --docs-governance-split` (advisory exit 0).

## Feature area registry

Hard constraint after every implementation:

1. Update [docs/feature-areas.yaml](../../docs/feature-areas.yaml)
2. Review/update `docs/` per [docs-maintenance](../docs-maintenance/SKILL.md)

| Change | Registry action |
| ------ | ----------------- |
| New file | Add under touched area `paths` / `tests` |
| New surface | New area entry with summary, paths, related |
| Renamed/removed file | Update or remove stale paths |
| New test file | Add under `tests` for area |
| New stable handler | Add under `handlers` |
| New agent/kanban rule | Add under Agent Workflow `paths`; sync AGENTS area table |

```bash
python scripts/resolve_feature_areas.py "Render Preview"
```
