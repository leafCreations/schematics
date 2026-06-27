# Kanban Markdown — Reference

**Lifecycle and gates:** [SKILL.md](SKILL.md). **Card-type constraints:** scoped `kanban-*.mdc` rules —
do not duplicate who-writes-what tables here; link to the matching rule. Signature:
`governance-compact-kanban-split` (gc1 — SKILL ≤ ~400 lines lifecycle; this file on demand).

Load this file for templates, section-order examples, file format, and audit checklist detail.

## Label Paths and Label Methods

Repo-relative paths in **`## Label Paths`**; symbols in **`## Label Methods`** — card body, not frontmatter.

### Example (agent after card review)

```markdown
## Label Paths

- `ui/main_window.py`
- `ui/reload.py`
- `tests/test_main_window.py`

## Label Methods

- `ui/main_window.py` — `MainWindow._on_open_structure`, `MainWindow._restart_editor_for_structure`
- `ui/reload.py` — `open_structure_in_editor_process`
- `tests/test_main_window.py` — `test_pick_structure_stage_*` (add: open while preview render active)
```

### Feature card section order

1. `# Title` + user story
2. `## Acceptance Criteria`
3. `## Out of Scope` (optional)
4. `## Feature Areas` (user)
5. `## Label Paths` (agent)
6. `## Label Methods` (agent)
7. `## Decisions` (agent)
8. `## Verify` (optional — user manual)
9. `## QA Review` (user, during review)

### Picking up a To Do card

1. Read **Feature Areas**; resolve via [docs/feature-areas.yaml](../../docs/feature-areas.yaml)
2. Write **Label Paths** + **Label Methods** before `in-progress`
3. Jump to Label Methods symbols first; grep for gaps
4. Map paths to tests via [targeted-testing](../targeted-testing/SKILL.md)
5. Missing all three → [repo-map](../repo-map/SKILL.md)

### User creates card (example)

```markdown
## Feature Areas

- `Render Tab`
- `Render Preview`
- `Render Selection`
```

### Agent after review (example)

```markdown
## Label Paths

- `ui/widgets/preview_panel.py`
- `ui/main_window.py`
- `tests/test_preview_panel.py`

## Label Methods

- `ui/widgets/preview_panel.py` — `PreviewPanel._set_zoom_factor`, `PreviewPanel.reset_zoom_to_default`
- `ui/main_window.py` — `MainWindow._on_tab_changed`
- `tests/test_preview_panel.py` — `test_preview_panel_zoom_scales_pixmap`
```

## Feature cards

**Rule:** [kanban-feature-cards.mdc](../../rules/kanban-feature-cards.mdc).

| Section | Who | When |
| ------- | --- | ---- |
| Story, **Feature Areas**, optional AC | User | Creation |
| **Label Paths**, **Label Methods**, **Decisions**, AC | Agent | Pre-implementation review |

**Do not** use Corrective Action or Response on feature cards.

### Feature card workflow

```text
User assigns → pre-implementation review → Label Paths + Label Methods
  → prior lessons gate → Decisions → in-progress → implement
  → pytests + registry + docs → AC [x] → review → user Verify/QA → done → lessons
```

## Bug cards

**Rule:** [kanban-bug-cards.mdc](../../rules/kanban-bug-cards.mdc). **Corrective Action** — not Decisions.

**Frontmatter:** `labels: ["bug"]` (inline JSON array).

### Who writes what

| Section | Who |
| ------- | --- |
| Steps to Reproduce, Current/Expected Behavior, Feature Areas | User |
| QA Review | User (during Review) |
| Root Cause, AC, Out of Scope, Label Paths, Label Methods, Corrective Action | Agent |

**Legacy:** `## What happens` → **Current Behavior**.

### Recommended section order

1. `# Title`
2. Steps to Reproduce, Current/Expected Behavior (user)
3. Root Cause, AC, Out of Scope (agent)
4. Feature Areas (user)
5. Label Paths, Label Methods, Corrective Action (agent)
6. Verify (optional), QA Review (user)

### Gates

| Gate | Requirement |
| ---- | ----------- |
| Before `in-progress` | User sections + agent sections filled |
| Before implementation | Corrective Action concrete — not TBD |
| Before `review` | AC `[x]`; pytests; registry + docs |

### Example Corrective Action

```markdown
## Corrective Action

- Add `_preview_stale` on `MainWindow`; set after successful save paths.
- `_ensure_preview_render()`: skip cached PNG short-circuit when stale.
- `_on_tab_changed`: call `_ensure_preview_render()` when Viewer tab selected.
- Tests in `tests/test_render_preview.py`; update `docs/ui.md` Viewer section.
```

## Commit-issue cards

**Rule:** [kanban-commit-issue-cards.mdc](../../rules/kanban-commit-issue-cards.mdc). Auto-created by
`scripts/on_pre_commit_failure.sh` only when `PRE_COMMIT=1` (actual **`git commit`**). Manual agent
runs of hook scripts do **not** spawn cards — Signature: `precommit-no-card-on-manual-hook`.

### Who writes what

| Section | Who |
| ------- | --- |
| Problem, Failed Tests, Staged files | Capture script |
| Root Cause, Corrective Action | Agent (on user **review**) |
| Label Paths, Label Methods | Agent (optional) |

### Reusable pattern? (on review)

If hook/pytest pattern is reusable:

1. Row in [pre-commit-workflow/reference.md](../pre-commit-workflow/reference.md) § Failure patterns
2. Cite **Signature** in [testing.mdc](../../rules/testing.mdc)
3. Note Signature in Corrective Action

### Workflow

```text
git commit fails → todo commit-issue card
User: review → Root Cause + Corrective Action (no code)
User approves → implement → review → done
```

Skip card: `SKIP_COMMIT_ISSUE_CARD=1 git commit …`

## Agent cards

**Rule:** [kanban-agent-cards.mdc](../../rules/kanban-agent-cards.mdc). **`## Feature Area`** (singular).

### Who writes what

| Section | Who |
| ------- | --- |
| Description, Feature Area | User |
| Label Paths, Label Methods, AC, Decisions | Agent |
| QA Review | User (optional) |

Do **not** use Corrective Action, Root Cause, or Response.

### Label Methods (governance)

Include scripts, skills/rules sections, registry docs, tests. Example symbols:

- `scripts/foo.py` — `function_name`
- `.cursor/skills/kanban-markdown/reference.md` — `§ Agent cards`
- `AGENTS.md` — `### Card types`

### Recommended section order

1. Description, Feature Area (user)
2. Label Paths, Label Methods, AC, Decisions (agent)
3. Verify, QA Review

### Spawn phased agent card series

When user asks for multi-step governance epic:

1. One **todo** card per phase — never Backlog
2. `labels: ["agent"]`, `epic: "{PascalCase}"`, `order` (`lc0`, `gs0`, …)
3. User: Description + Feature Area on every card
4. Agent at spawn: Label Paths, Label Methods, AC, Decisions; optional Context with phase table
5. **Hybrid agent cards:** product Feature Area + thin helper; keep `labels: ["agent"]`
6. **Spawn from Out of Scope:** `## Spawned follow-up cards` on parent; correct label per type
7. **Out-of-order close:** when a later phase (e.g. lc1) lands before an earlier spec card (lc0),
   grep the target doc section first — extend with gaps (**Related workflow**, **Inputs**, rollout
   note) rather than rewriting; record the skew in **Decisions** (`**Prior lessons**` or dated note).

**Example epics:** `LessonsCoverageMetric` (lc0–lc3); `LessonsReferenceIndex` (li0–li3);
`GovernanceAreaSchema` (gs0–gs3); `GovernanceCompact` (gc0–gc7); `ArtifactsDocYaml` (ap0–ap1).

### Example Description (user)

```markdown
## Description

Add kanban label `agent` for governance cards. Keep Python lines ≤ 100 characters.
Document workflow in skills and rules.
```

```markdown
## Feature Area

- `Agent Workflow`
```

## Inquiry cards

**Rule:** [kanban-inquiry-cards.mdc](../../rules/kanban-inquiry-cards.mdc). No Decisions / CA / AC on card.

### Who writes what

| Section | Who |
| ------- | --- |
| Description | User |
| Feature Areas | User (optional) |
| Label Paths, Label Methods | Agent (when Feature Areas set) |
| Response | Agent |

### Inquiry workflow

```text
User assigns → optional Label Paths/Methods → in-progress → research (read-only)
  → Response on card → review → user may spawn feature/bug/agent cards
```

### Gates

| Gate | Requirement |
| ---- | ----------- |
| Before `in-progress` | Description present |
| Before `review` | Response complete |
| Code | None by default |

### Example Response

```markdown
## Response

### Answer

Preview PNGs are session-scoped under `output/schematics/_preview/{session}/`.

### Key paths

- `ui/main_window.py` — `_ensure_preview_render()`, `_preview_stale`
- `docs/ui.md` — Viewer tab behavior

### Suggested follow-up cards

**Bug: Preview stale after save**
- Feature Areas: `Render Preview`, `Render Tab`
- AC draft: After save, Viewer re-renders when session PNGs are stale.
```

## Spawn from inquiry

Full procedure: [SKILL.md § Spawn from inquiry](SKILL.md#spawn-from-inquiry).

### Feature card body at spawn

| Section | Content |
| ------- | ------- |
| `# Title` | From recommendation |
| **Acceptance Criteria** | Draft `[ ]` bullets |
| **Out of Scope** | From inquiry boundaries |
| **Feature Areas** | Backtick-quoted labels |
| **Label Paths** | Resolved via feature-areas.yaml |
| **Label Methods** | Registry handlers + inquiry evidence |
| **Decisions** | Concrete plan |
| **Context** | Parent inquiry id; phase number |

**Spawn label by work type:** `feature`/`bug` product; **`agent`** governance; **`inquiry`** research.

### Drift spawn card skeleton (`check_governance_parity.py`)

Auto-spawned cards must include **all label-type sections** before `in-progress` — use `_TBD_`
placeholders, not omit sections. Signature: `lessons-coverage-ci-drift`.

| Label | Sections at spawn (after `## Alert` + paths) |
| ----- | ---------------------------------------------- |
| `feature` (GovernanceDriftAlert) | **Feature Areas**, **Label Paths**, **Label Methods**, **Decisions**, **Acceptance Criteria** |
| `agent` (LessonsCoverageMetric drift) | **Description** (from corrective-action text), **Feature Area**, **Label Paths**, **Label Methods**, **Decisions**, **Acceptance Criteria** |

**Registry Label Methods drift:** `create_drift_alert_cards` consolidates multiple missing-handler
alerts for the **same source kanban card** into one todo card (bullet list of symbols). Card id:
`governance-drift-registry-{hash:card}` — Signature: `governance-drift-spawn-consolidate-by-source-card`.

Do **not** use **Corrective Action** on spawned `feature`/`agent` cards — bug/commit-issue only.

**Spawn inquiry from render QA:** 2D vs 3D parity questions → `labels: ["inquiry"]` todo card; link from parent.

**Spawn from inquiry (OrbitRenderClass example):** parent inquiry Response + implementation plan →
`agent` todo (doc/test parity) + deferred `feature` todo (registry YAML when trigger fires); parent
`## Spawned feature cards` table with epic `OrbitRenderClass` order a0/a1.

**Spawn from epic review (Card Done enforcement, 2026-06-27):** user discussion → implement queue:

| order | card | epic |
| ----- | ---- | ---- |
| aK | `agent-card-done-agent-move-qa-complete-2026-06-27` | GovernanceCompact (gc8) |
| aM | `agent-lessons-coverage-lc4c-parser-templates-c1b-2026-06-27` | LessonsCoverageMetric (lc4c — Option C) |
| aN | `agent-lessons-coverage-lc4b-c4-per-card-threshold-2026-06-27` | LessonsCoverageMetric (lc4b — partial B) |

Supersedes monolithic `agent-lessons-coverage-enforcement-option-b-2026-06-27` (aL). Link queue in
**Context**; no parent inquiry table required.

**Spawn from Q3 Option C (2026-06-27):** epic-completion audit + gc7 file checks — epic
`GovernanceEpicLifecycle`:

| order | card | phase |
| ----- | ---- | ----- |
| aO | `agent-governance-epic-completion-audit-2026-06-27` | gel0 — epic audit workflow, closed-epic names |
| aP | `agent-governance-gc7-handoff-duplication-pair-2026-06-27` | gel1 — parity handoff dup check |
| aQ | `agent-governance-gc7-forward-feedback-audit-2026-06-27` | gel2 — `--forward-feedback-audit` |

**Implement order (full Q3 queue):** aK → aM → aN → aO → aP → aQ → aR (gel3 archive batch).
Anchor card maintains **`## Epic cards`** table; on epic complete run § Epic audit (gel0). Cross-epic
initiative **`CardDoneGovernanceLoop2026`** — manifest on gel3; batch archive § Archive group.

| order | card | phase |
| ----- | ---- | ----- |
| aR | `agent-governance-gel3-archive-group-batch-2026-06-27` | gel3 — cross-epic archive group batch |

### Epic audit (gel0 — agent turn)

When user confirms epic complete (no active cards with that `epic:`):

1. Verify **`## Epic cards`** manifest — all rows `done` / archived / superseded.
2. Run `python3 scripts/check_governance_parity.py` (spawn fix cards unless audit-only).
3. When `done/` exists: `python3 scripts/check_lessons_coverage.py --json`.
4. Governance epics: `--line-counts`; optional `--forward-feedback-audit` after gel2.
5. Agent runtime smoke: `@` bug card → **Corrective Action** (not Decisions).
6. Write **`## Epic audit (YYYY-MM-DD)`** on anchor; append epic to closed registry.
7. **Do not** reuse closed `epic:` on new cards — new PascalCase epic for follow-ups.
8. **Do not** batch-move to `archived/` when members have open **`archiveGroup:`** — defer to § Archive group.

Quarterly `create_governance_audit_card.py` is optional backstop only (not primary cadence).
Signature: `governance-epic-completion-audit`.

### Archive group (gel3 — cross-epic batch)

When a feature spans **multiple epics**, **epic audit** and **batch archive** are separate gates.

| Gate | Trigger | Cards move to `archived/`? |
| ---- | ------- | -------------------------- |
| Epic audit | No active cards for one `epic:` + user confirms | **No** — stay in `done/` if `archiveGroup:` set |
| Archive group complete | All manifest rows `done` / archived / superseded + user confirms | **Yes** — batch listed members only |

**Manifest SSOT:** anchor card **`## Archive group: {PascalCaseName}`** table (order, card, epic,
status). Members carry matching **`archiveGroup:`** frontmatter (optional `epic:` between
`assignee` and `dueDate`).

**CardDoneGovernanceLoop2026** (2026-06-27): aK (GovernanceCompact gc8), aM/aN (LessonsCoverageMetric
lc4), aO–aR (GovernanceEpicLifecycle gel0–gel3). Queue scope only — not historical done cards under
the same epic names.

**Archive group turn (agent):**

1. Verify manifest — every row `done` / `archived` / `superseded`.
2. User confirms `archive group {Name} complete`.
3. Move `done/{id}.md` → `archived/{id}.md` for **listed members**; keep `status: "done"`.
4. Refresh active card links (`done/` → `archived/`); Signature `kanban-card-stale-dependency-links`.
5. Write **`## Archive batch (YYYY-MM-DD)`** on anchor; retire archive group name for new spawns.

**Card Done:** move to `done/` only — never archive on the same turn.

**Superseded never-implemented** cards may go to `archived/` early; remove from manifest or mark
`superseded`.

Signature: `governance-archive-group-batch`.

## Prior lessons gate

Canonical procedure: [SKILL.md § Prior lessons gate](SKILL.md#prior-lessons-gate).
Rule: [kanban-prior-lessons-gate.mdc](../../rules/kanban-prior-lessons-gate.mdc).

### Resolver arguments

| Argument | Source |
| -------- | ------ |
| `--epic` | Frontmatter `epic` |
| Positional labels | Feature Areas or Feature Area |
| `--paths` | Prefixes from Label Paths |

### Read matched artifacts

| Section | Action |
| ------- | ------ |
| Registry lesson pointers | Grep Signatures; skim lesson_docs |
| Done/archived Lessons captured | Full card when index insufficient |
| Open commit-issue | Problem / Failed Tests; grep Signatures |
| Feature area docs | Skim listed docs before Decisions |

**Skip:** inquiry research-only; ad-hoc fixes without card.

## Verify

**Agent (always):** `scripts/pre-commit-pytest.sh` on staged paths — feature/bug/agent before Review.
**Inquiry:** no pytest unless code changed.

**Do not** put pytest lines in **`## Verify`** on cards — implicit agent work.

## Decisions

**Feature and agent cards only.**

Write after pre-implementation review, before `in-progress`. Concrete bullets — not TBD.

```markdown
## Decisions

- Group dropdown in `PreviewPanel` toolbar; hidden when only one group.
- Per-Y PNGs under `output/schematics/_preview/{session}/`.
- Reuse `RenderWorker` + save-first pattern from render-selection card.
```

## Corrective Action

**Bug and commit-issue cards only.**

Pair with **Root Cause** — root cause explains why; corrective action states what to change.

## Acceptance Criteria

**Feature and bug cards.** All satisfied bullets **`[x]`** before **Review**.

| Rule | Detail |
| ---- | ------ |
| Format | `- [x]` / `- [ ]` — not `- []` |
| All met | Every AC `[x]` unless user defers |
| QA Review | Check off AC when QA completes scope |

```markdown
## Acceptance Criteria

- [x] Render dropdown includes "Site Facades"
- [x] Each Direction displays as individual PNG
- [x] PNGs shown as thumbnails
```

## QA Review

**User** populates during Review. Agent implements when user asks.

1. Read QA Review + Feature Areas + Label Paths + Label Methods + Out of Scope
2. Pre-QA review — clarify ambiguities
3. Implement open bullets; staged pytests
4. Mark `[x]`; bump `modified`; stay in **review**

**Spawn bug cards from QA Review:** parent **QA Review** + **Spawned bug cards** table; child `labels: ["bug"]`;
set `order` (`a0`, `a1`, …) for implementation sequence.

```markdown
## QA Review

- [ ] Preview dropdown should disable while render is in progress
- [x] Caption text should not show full filesystem path
```

## User-reported QA fixes

Rule: [kanban-review-qa.mdc](../../rules/kanban-review-qa.mdc). Summary: [SKILL.md](SKILL.md#user-reported-qa-fixes).

| Card type | Record under |
| --------- | ------------ |
| bug | **Corrective Action** |
| feature, agent | **Decisions** |

```markdown
**QA follow-up (2026-06-25):** Black slab tops — `_resolve_orbit_slab_face_texture` +
`test_orbit_slab_face_textures_are_opaque`. **Labels:** appended `helpers/orbit_greedy_mesh.py`.
```

### Label refresh checklist

| Section | When |
| ------- | ---- |
| Feature Areas | Fix touched new product area |
| Label Paths | New/edited path not on card |
| Label Methods | New symbol or test name |
| feature-areas.yaml | Durable path/handler for area |

## Card Done — lessons learned capture

Canonical summary: [SKILL.md § Card Done](SKILL.md#card-done--lessons-learned-capture).

### Artifact update table

| Lesson type | Update |
| ----------- | ------ |
| Area workflow | Matching area skill |
| Hard constraint | Scoped `.mdc` rule |
| User-visible behavior | `docs/` per docs-maintenance |
| New symbols/paths | feature-areas.yaml handlers + Label Methods |
| Cross-cutting failure | agent-self-evaluation/reference.md (**Signature** in rules) |
| Prior-lessons discovery | agent-triage/reference.md § Lessons by area |
| Card Done forward feedback | `## Forward-looking feedback` on done card after Lessons captured — Signature: `card-done-forward-feedback` |
| Lessons coverage audit | `check_lessons_coverage.py` (C1–C4); `--strict` for C3 without epic-only match — Signature: `lessons-coverage-strict-consumption` |
| C4 Prior lessons block | No line starting with `**` inside block after header; cite done stems (`YYYY-MM-DD.md`, commit-issue `T` timestamps, drift hash ids) — Signature: `lessons-coverage-c2-c3-audit` |
| GovernanceDriftAlert registry path (lc1 scripts) | Extend `_SCHEMA_INTERNAL_PATHS` in `check_governance_parity.py` — not AGENTS area table columns; sibling spawn cards (`lessons_coverage_lib.py`, hook script, test file) share one fix — Signature: `governance-area-schema-parity-tests`, `lessons-coverage-c2-c3-audit` |
| Superseded GovernanceDriftAlert sibling | Mark **Decisions** `Superseded` + link to parent `done/{id}.md`; AC `[x]`; `review` → user/agent `done/` — no code; cite parent **Lessons captured** |

### Lessons captured example

```markdown
## Lessons captured (2026-06-27)

- **Symptom:** …
- **Fix:** …
  - artifacts: skill:ui-change, rule:testing.mdc#orbit-animated-texture-strip, sig:orbit-animated-texture-strip
```

Prefixes: `skill:`, `rule:`, `doc:`, `sig:`, `test:`. Registry yaml: `doc:lessons-index.yaml` (explicit extension). Inline `` `sig:slug` `` on lesson bullets is indexed by `build_lessons_index.py` — Signature: `lessons-index-inline-sig-backtick`.

### Forward-looking feedback

**After** `## Lessons captured` on **`feature` / `bug` / `agent` / `commit-issue`** Done only —
not every turn, not on **`inquiry`**. Signature: `card-done-forward-feedback`.

Six categories (≥1 item each): governance, skill, rule, codebase, prompt pattern, routing.
Items must reflect **this card's** outcomes — not generic placeholders.

**Per-item fields**

| Field | Required | Notes |
| ----- | -------- | ----- |
| **Question** | yes | Card-specific forward-looking question |
| **Risk Level** | yes | 1–5 |
| **Priority** | yes | 1–2 Low; 3 Medium; 4–5 High (derived from risk) |
| **Impact Scope** | yes | **local**, **multi-card**, or **system-wide** |
| **References** | yes | Rules, skills, signatures, scripts, governance paths |
| **Mitigation** | max-tier only | Concrete step for **every** item at the card's highest risk level |
| **Detail** | risk ≥ 3 | Failure-mode context |
| **Importance** | when tied | **Primary** / **Secondary** / **Tertiary** — see ranking below |

**Mandatory max risk:** the block must include ≥1 item at the card's highest risk level (do not
cap all items at Low when outcomes warrant Medium+).

**Importance labels:** when ≥2 items share the card's max risk, assign exactly one **Primary** and
label the rest **Secondary**; optional **Tertiary** on lower-tier contextual items. A sole
max-tier item needs no Importance label (implicit top item).

**Ranking** (Primary selection; Secondary sort; top-3 chat backfill):

1. Impact Scope: system-wide > multi-card > local
2. Category: Governance > Routing > Rule > Skill > Codebase > Prompt pattern
3. Failure-mode severity (tie-breaker)

**Top-3 in chat (Card Done turn):** after writing the card block, surface up to three items in the
assistant's final response — Primary first, then highest-ranked Secondary items; backfill from
next-highest risk using the same sort until three items or the list is exhausted. Place
`### Top forward feedback` before `### Files used` — [agent-self-evaluation/SKILL.md](../agent-self-evaluation/SKILL.md) §7.

**Backward compatibility:** legacy done cards without Impact Scope / References / Mitigation remain
valid; no retroactive edits. C1–C4 lessons coverage does not parse forward-feedback sections.

```markdown
## Forward-looking feedback (2026-06-27)

### Governance
- **Question:** Should `--line-counts` be required on every GovernanceCompact Card Done?
  **Risk Level:** 4 | **Priority:** High | **Importance:** Primary
  **Impact Scope:** system-wide
  **References:** `check_governance_parity.py --line-counts`, `kanban-agent-cards.mdc`, sig:governance-compact-baseline
  **Mitigation:** Add one-line `--line-counts` bullet to GovernanceCompact Card Done AC templates.
  **Detail:** Without a gate, compaction phases may ship without measurable before/after proof.

### Skill
- **Question:** Did kanban-markdown § Card Done need a reference split for the feedback example?
  **Risk Level:** 2 | **Priority:** Low | **Importance:** Tertiary
  **Impact Scope:** local
  **References:** skill:kanban-markdown, sig:governance-compact-kanban-split

### Rule
- **Question:** Should kanban-review-qa.mdc cite tightened forward-feedback fields alongside lessons?
  **Risk Level:** 4 | **Priority:** High | **Importance:** Secondary
  **Impact Scope:** multi-card
  **References:** rule:kanban-review-qa.mdc, sig:card-done-forward-feedback
  **Mitigation:** Grep all scoped `kanban-*-cards.mdc` Card Done bullets when reference § changes.
  **Detail:** Card Done checklists drift when only SKILL.md updates.

### Codebase
- **Question:** Does `build_lessons_index.py` need to index forward-feedback sections?
  **Risk Level:** 1 | **Priority:** Low
  **Impact Scope:** local
  **References:** `scripts/build_lessons_index.py`, sig:card-done-forward-feedback

### Prompt pattern
- **Question:** Should agents stop asking §6 improvement questions when user says Done?
  **Risk Level:** 3 | **Priority:** Medium
  **Impact Scope:** multi-card
  **References:** skill:agent-self-evaluation, sig:card-done-forward-feedback
  **Detail:** Duplicate feedback (chat §6 + card block) wastes tokens and splits the audit trail.

### Routing
- **Question:** Should AGENTS.md Classify **Done** rows mention top-3 chat surfacing?
  **Risk Level:** 3 | **Priority:** Medium
  **Impact Scope:** system-wide
  **References:** AGENTS.md, skill:agent-triage, sig:card-done-forward-feedback
  **Detail:** Agents routing Card Done from AGENTS alone may skip chat surfacing without an explicit row.
```

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
- User `review` → `done`: `completedAt`; move to `done/`

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
- [ ] **Docs:** docs/development.md Cursor workflow ↔ AGENTS + consistency links
- [ ] **Lessons coverage:** `check_lessons_coverage.py` when done/ exists; parity script `Lessons coverage drift alert:` matches composite &lt; 75%
- [ ] **Kanban cards:** Feature Areas cards have Label Paths + Label Methods before `in-progress`

**Output:** drift bullets under **## Audit findings** — do not silently fix during audit turn.

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
