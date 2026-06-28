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

## Cursor mode gates (Plan / Inquire / verbs)

Epic **`KanbanCursorModeGates`** (cm0–cm3). Aligns **Cursor UI mode** (Ask / Plan / Agent), user
**prompt verbs**, and **kanban card file edits**. Scoped rules implement in **cm1**
([kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2, [kanban-plan-cards.mdc](../../rules/kanban-plan-cards.mdc)).
Signature: `kanban-cursor-mode-gates`. Complements `kanban-prompt-ask-vs-agent`.

### Mode detection

Agents **cannot** probe Cursor UI mode from repo scripts. Infer from **session context** (system
reminders such as “Ask mode is active”, Plan Mode, or default Agent). On mismatch for **`Plan @card`**
or **`Inquire @card`** → **stop**; tell the user which Cursor mode to select and retry.

### Verb / mode / card-edit matrix (default)

| User prompt (contains) | Required Cursor mode | Edit `.devtool/features/*.md`? | Product code? |
| ---------------------- | -------------------- | ------------------------------ | ------------- |
| `review @card` / `review …` only | Any | **No** — chat-only always | No |
| `Inquire @card` / `Inquire …` | **Ask** | **No** — research in chat | No |
| `Plan @card` / `Plan …` | **Plan** | **No** — plan/roadmap in chat | No |
| `update …` / `update @card` | **Agent** | **Yes** (card body) | Only if card type allows |
| `plan approved` / `approved` / `plan … approved` | **Agent** | **Yes** on **`plan`** card — write **Recommendation** | No |
| `implement …` / `spawn …` / `Done` / … | **Agent** | Per [kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2 | Per card type |

**Card-update allowlist:** agents edit kanban card markdown only when the prompt includes
`update …`, `plan approved`, `approved`, `plan … approved`, or the rare compounds below — not on
bare `@path`, `review …`, `Inquire …`, or `Plan …` alone.

**`approved` scope:** valid only when continuing an **approved Plan discussion** on a card with
`labels: ["plan"]` — not a generic commit verb on feature/bug cards.

**Deprecated:** `Kanban: answer inquiry on …` as same-turn **Response** write — use **`Inquire`**
(Ask, chat) then **`update @inquiry-card`** (Agent) after discussion.

### Rare compound verbs (single-turn exceptions)

Document only — **not** the default workflow. User explicitly accepts skipping the discuss-then-approve
gate.

| Compound prompt | Phase A | Phase B (same turn) |
| --------------- | ------- | ------------------- |
| **`review and update @card`** | Ask-style research (read-only) | Agent writes card sections |
| **`plan and update @card`** | Plan Mode exploration + structured plan | Agent writes **Recommendation** on **`plan`** card |

Use when the user trusts one-turn persistence; otherwise prefer default two-phase flow.

### Plan cards

**Label:** `labels: ["plan"]`. **Rule:** [kanban-plan-cards.mdc](../../rules/kanban-plan-cards.mdc).

| Section | Who | When on card |
| ------- | --- | ------------ |
| **Description** | User | Creation |
| **Feature Areas** | User (optional) | Creation |
| **Recommendation** | Agent | **After** `plan approved` / `update` — not during `Plan @card` |
| **Product Paths** / **Product Methods** | Agent (optional) | When spawning or area set — after approval |
| **Spawned …** tables | Agent | After user asks to spawn |

**Do not** use **Decisions**, **Corrective Action**, or **Acceptance Criteria** on plan cards.
Card Done: move to `done/` only — **no** lessons or forward feedback (same as inquiry).

#### Plan workflow (default)

```text
User assigns plan card → Plan @card (Plan Mode) → discuss in chat
  → user: plan approved / approved / update @card (Agent)
  → write ## Recommendation on card → review
  → optional spawn feature/bug/agent cards
  → done (move only)
```

#### Example Recommendation (on card, post-approval)

```markdown
## Recommendation

### Summary

Split orbit preview banner work into three feature cards (banner, sign, campfire) with shared
Product Paths under `ui/widgets/orbit_preview_widget.py`.

### Phased roadmap

1. Banner overlay geometry (feature-orbit-preview-banner)
2. Sign attachable routing (feature-orbit-preview-sign)
3. Campfire particle stub (feature-orbit-preview-campfire)

### Suggested follow-up cards

| order | label | title |
| ----- | ----- | ----- |
| … | feature | … |
```

## Feature cards

**Rule:** [kanban-feature-cards.mdc](../../rules/kanban-feature-cards.mdc).

| Section | Who | When |
| ------- | --- | ---- |
| Story, **Feature Areas**, optional AC (behavior) | User | Creation |
| **Product Paths**, **Product Methods**, **Tests**, **Docs**, **Decisions**, AC | Agent | Pre-implementation review |

Legacy open cards may use **Label Paths** / **Label Methods** until ks2 — see § Kanban card scope.

**Do not** use Corrective Action or Response on feature cards.

### Feature card workflow

```text
User assigns → pre-implementation review → Product + Tests + Docs sections
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
| Root Cause, AC (behavior), Out of Scope, Product Paths, Product Methods, Tests, Docs, Corrective Action | Agent |

Legacy: **Label Paths** / **Label Methods** acceptable until ks2.

**Legacy:** `## What happens` → **Current Behavior**.

### Recommended section order

1. `# Title`
2. Steps to Reproduce, Current/Expected Behavior (user)
3. Root Cause, AC, Out of Scope (agent)
4. Feature Areas (user)
5. Product Paths, Product Methods, Tests, Docs, Corrective Action (agent)
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

**Tests:** `tests/test_render_preview.py` — stale-after-save cases.

**Docs:** `docs/ui.md` — Viewer section.
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
| Product Paths, Product Methods, Tests, Docs | Agent (optional) |

Legacy: **Label Paths** / **Label Methods** until ks2.

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
| Product Paths, Product Methods, Tests, Docs, AC (behavior), Decisions | Agent |
| QA Review | User (optional) |

Legacy: **Label Paths** / **Label Methods** until ks2.

Do **not** use Corrective Action, Root Cause, or Response.

### Product Methods (governance)

Include scripts, skills/rules sections, registry docs — not pytest (use **Tests**). Example symbols:

- `scripts/foo.py` — `function_name`
- `.cursor/skills/kanban-markdown/reference.md` — `§ Agent cards`
- `AGENTS.md` — `### Card types`

### Recommended section order

1. Description, Feature Area (user)
2. Product Paths, Product Methods, Tests, Docs, AC, Decisions (agent)
3. Verify, QA Review

### Spawn phased agent card series

When user asks for multi-step governance epic:

1. One **todo** card per phase — never Backlog
2. `labels: ["agent"]`, `epic: "{PascalCase}"`, `order` (`lc0`, `gs0`, …)
3. User: Description + Feature Area on every card
4. Agent at spawn: Product Paths, Product Methods, Tests, Docs, AC, Decisions; optional Context with phase table
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
Cursor mode: **`Inquire @card`** + **Ask Mode** — see § [Cursor mode gates](#cursor-mode-gates-plan--inquire--verbs).

### Who writes what

| Section | Who |
| ------- | --- |
| Description | User |
| Feature Areas | User (optional) |
| Product Paths, Product Methods | Agent (when Feature Areas set) — after **`update`** |
| Response | Agent — **on card only after** `update …` / `review and update` (not on `Inquire` alone) |

### Inquiry workflow (default — cm0)

```text
User assigns → optional Product scope → in-progress
  → Inquire @card (Ask Mode) → research + answer in chat
  → user discusses → update @inquiry-card (Agent) → write ## Response on card → review
  → user may spawn feature/bug/agent/plan cards
  → done (move only — no Card Done lessons)
```

**Rare:** `review and update @inquiry-card` — research + **Response** on card same turn (§ Cursor mode gates).

### Gates

| Gate | Requirement |
| ---- | ----------- |
| Before `in-progress` | Description present |
| Before `review` | **Response** on card (after `update` / approval path) |
| **`Inquire @card`** | Ask Mode — **no** card file edits |
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
| **Acceptance Criteria** | Draft `[ ]` behavior bullets — no pytest in AC |
| **Out of Scope** | From inquiry boundaries |
| **Feature Areas** | Backtick-quoted labels |
| **Product Paths** | Resolved via feature-areas.yaml (no `tests/`) |
| **Product Methods** | Registry handlers + inquiry evidence |
| **Tests** | Files, Methods, Verify (agent) |
| **Docs** | From area `docs:` + § hints |
| **Decisions** | Concrete plan |
| **Context** | Parent inquiry id; phase number; optional parent **`ff-*`** id when spawned from forward-feedback index (`resolve_forward_feedback.py --link`) |

Legacy spawn bodies may still use **Label Paths** / **Label Methods** until ks1 parser dual-read ships.

**Spawn label by work type:** `feature`/`bug` product; **`agent`** governance; **`inquiry`** research.

### Drift spawn card skeleton (`check_governance_parity.py`)

Auto-spawned cards must include **all label-type sections** before `in-progress` — use `_TBD_`
placeholders, not omit sections. Signature: `lessons-coverage-ci-drift`.

| Label | Sections at spawn (after `## Alert` + paths) |
| ----- | ---------------------------------------------- |
| `feature` (GovernanceDriftAlert) | **Feature Areas**, **Product Paths**, **Product Methods**, **Tests**, **Docs**, **Decisions**, **Acceptance Criteria** |
| `agent` (LessonsCoverageMetric drift) | **Description** (from corrective-action text), **Feature Area**, **Product Paths**, **Product Methods**, **Tests**, **Docs**, **Decisions**, **Acceptance Criteria** |

Until ks1 ships, parity spawn may still emit **Label** headings — parsers accept both. Use `_TBD_`
placeholders for Product/Tests/Docs when unknown at spawn time.

**Registry Product Methods drift:** `create_drift_alert_cards` consolidates multiple missing-handler
alerts for the **same source kanban card** into one todo card (bullet list of symbols). Card id:
`governance-drift-registry-{hash:card}` — Signature: `governance-drift-spawn-consolidate-by-source-card`.
Parsers dual-read **Label Methods** until ks2; spawn output uses **Product Methods** (ks1).
**Parser SSOT (ks1):** `scripts/resolve_prior_lessons.py` `extract_label_paths()` — Product Paths,
legacy Label Paths, and **Tests → Files**; `check_governance_parity.extract_label_method_symbols()`
— Product + Label Methods headings.

Do **not** use **Corrective Action** on spawned `feature`/`agent` cards — bug/commit-issue only.

**Spawn inquiry from render QA:** 2D vs 3D parity questions → `labels: ["inquiry"]` todo card; link from parent.

**Spawn from inquiry (OrbitRenderClass example):** parent inquiry Response + implementation plan →
`agent` todo (doc/test parity) + deferred `feature` todo (registry YAML when trigger fires); parent
`## Spawned feature cards` table with epic `OrbitRenderClass` order a0/a1.

**Spawn from plan (OrbitFunctionalFaceTextures example):** plan card Recommendation + user
`update`/`spawn` → two **`bug`** todos (a0 texture resolution, a1 facing faces + merged bed
head/foot top split); parent **`## Spawned feature cards`** + child **Product** / **Tests** /
**Docs** / **Corrective Action**; epic on parent + children; implement a0 before a1 when ordered.

**Spawn from epic review (Card Done enforcement, 2026-06-27):** user discussion → implement queue:

| order | card | epic |
| ----- | ---- | ---- |
| aK | `agent-card-done-agent-move-qa-complete-2026-06-27` | GovernanceCompact (gc8) |
| aM | `agent-lessons-coverage-lc4c-parser-templates-c1b-2026-06-27` | LessonsCoverageMetric (lc4c — Option C) |
| aN | `archived/agent-lessons-coverage-lc4b-c4-per-card-threshold-2026-06-27` | LessonsCoverageMetric (lc4b — archived) |

Supersedes monolithic `agent-lessons-coverage-enforcement-option-b-2026-06-27` (aL). Link queue in
**Context**; no parent inquiry table required.

**Spawn from Q3 Option C (2026-06-27):** epic-completion audit + gc7 file checks — epic
`GovernanceEpicLifecycle`:

| order | card | phase |
| ----- | ---- | ----- |
| aO | `archived/agent-governance-epic-completion-audit-2026-06-27` | gel0 — epic audit workflow (archived) |
| aP | `archived/agent-governance-gc7-handoff-duplication-pair-2026-06-27` | gel1 — handoff dup check (archived) |
| aQ | `archived/agent-governance-gc7-forward-feedback-audit-2026-06-27` | gel2 — `--forward-feedback-audit` (archived) |

**Implement order (full Q3 queue):** aK → aM → aN → aO → aP → aQ → aR (gel3 archive batch).
Anchor card maintains **`## Epic cards`** table; on epic complete run § Epic audit (gel0). Cross-epic
initiative **`CardDoneGovernanceLoop2026`** — manifest on gel3; batch archive § Archive group.

**Spawn from card scope discussion (2026-06-27):** epic **`KanbanCardScope`** — **closed 2026-06-28**
(archived aU–aX; anchor `archived/agent-kanban-card-scope-ks0-schema-spec-2026-06-27.md`):

| order | card | phase |
| ----- | ---- | ----- |
| aU | `archived/agent-kanban-card-scope-ks0-schema-spec-2026-06-27` | ks0 — reference templates + ownership |
| aV | `archived/agent-kanban-card-scope-ks1-parsers-spawn-2026-06-27` | ks1 — resolve_prior_lessons + parity spawn |
| aW | `archived/agent-kanban-card-scope-ks2-governance-rollout-2026-06-27` | ks2 — kanban rules, AGENTS.md |
| aX | `archived/agent-kanban-card-scope-ks3-verify-hook-gate-2026-06-27` | ks3 — Tests verify + pre-commit gate |

**Closed** — do not reuse `epic: KanbanCardScope`. Signatures: `kanban-card-scope-schema`,
`precommit-pytest-scope-mismatch`.

**Spawn (2026-06-28):** epic **`KanbanCursorModeGates`** — Plan / Inquire Cursor mode gates (cm0–cm3):

| order | card | phase |
| ----- | ---- | ----- |
| aY | `agent-kanban-cursor-mode-cm0-schema-spec-2026-06-28` | cm0 — schema + reference | done |
| aZ | `agent-kanban-cursor-mode-cm1-scoped-rules-2026-06-28` | cm1 — plan rule + card-gates | done |
| b0 | `agent-kanban-cursor-mode-cm2-classify-rollout-2026-06-28` | cm2 — AGENTS + Classify SSOT | done |
| b1 | `agent-kanban-cursor-mode-cm3-verify-parity-2026-06-28` | cm3 — fingerprint + verify | done |

Implement **aY → aZ → b0 → b1**. Signature: `kanban-cursor-mode-gates`.

**Spawn (2026-06-29):** epic **`DocsGovernanceSplit`** — separate product `docs/` from governance
narrative; split oversized `docs/development.md` — **closed 2026-06-27** (gel0 audit on dg0 anchor;
`docs/epics-closed.yaml`; batch archived):

| order | card | phase |
| ----- | ---- | ----- |
| dg0 | `archived/agent-docs-governance-split-dg0-schema-spec-2026-06-29.md` | dg0 — layout schema + file map |
| dg1 | `archived/agent-docs-governance-split-dg1-split-development-2026-06-29.md` | dg1 — move prose; stub development.md |
| dg2 | `archived/agent-docs-governance-split-dg2-routing-rollout-2026-06-29.md` | dg2 — AGENTS/skills/rules refs |
| dg3 | `archived/agent-docs-governance-split-dg3-verify-parity-2026-06-29.md` | dg3 — grep + parity + gel0 close |

All phases complete (in `archived/`). Anchor: dg0 **`## Epic cards`** + **`## Epic audit`** +
**`## Archive batch`**. Signature: `docs-governance-split`.

**Spawn from forward-feedback registry discussion (2026-06-27):** epic **`ForwardFeedbackRegistry`**
**closed 2026-06-27** (gel0 audit on ff0 anchor; `docs/epics-closed.yaml`) — centralized gc5
question index + top-N by category:

| order | card | phase |
| ----- | ---- | ----- |
| ff0 | `archived/agent-forward-feedback-ff0-index-build-2026-06-27.md` | index + `resolve_forward_feedback.py` |
| ff1 | `archived/agent-forward-feedback-ff1-card-done-ingest-2026-06-27.md` | Card Done rebuild + dedup warnings |
| ff2 | `archived/agent-forward-feedback-ff2-resolution-tracking-2026-06-27.md` | status / spawned links |
| ff3 | `archived/agent-forward-feedback-ff3-metrics-advisory-2026-06-27.md` | stale metrics (advisory) |

All phases complete (in `archived/`). Anchor: ff0 **`## Epic cards`** + **`## Epic audit`** +
**`## Archive batch`**. Signatures:
`forward-feedback-index`, `forward-feedback-card-done-ingest`, `forward-feedback-resolution-tracking`,
`forward-feedback-stale-metrics`. Complements gel2 `governance-gc7-forward-feedback-audit` (card field
audit — not backlog SSOT).

| order | card | phase |
| ----- | ---- | ----- |
| aR | `archived/agent-governance-gel3-archive-group-batch-2026-06-27` | gel3 — archive group batch (archived) |
| aS | `archived/agent-governance-gel4-epic-completion-summary-2026-06-27` | gel4 — epic/initiative summary (archived) |

### Epic cards (anchor convention)

Multi-card epics use one **anchor** card (usually the first spawned member) with a **`## Epic cards`**
table the agent maintains on every spawn:

| Column | Purpose |
| ------ | ------- |
| `order` | Frontmatter `order` (`aO`, `aP`, …) |
| `card` | Stem or relative path |
| `status` | `todo` / `in-progress` / `review` / `done` / archived / superseded |

**Epic complete** (user confirms): no rows remain `todo`, `in-progress`, or `review` for that `epic:`.
Then run § Epic audit on the anchor — **not** the same turn as batch archive when `archiveGroup:` is
set (defer to § Archive group).

**Pre-spawn:** `python3 scripts/resolve_epic_cards.py --validate-new {EpicName}` — exit 1 when the
name is in [docs/epics-closed.yaml](../../docs/epics-closed.yaml). Follow-ups use a **new** PascalCase
epic (e.g. `LessonsCoverageMetric` closed → `LessonsCoverageMetricV2` or a themed rename).

### Epic audit (gel0 — agent turn)

When user confirms epic complete (no active cards with that `epic:`):

1. Verify **`## Epic cards`** manifest — all rows `done` / archived / superseded.
2. Run `python3 scripts/resolve_epic_cards.py --epic {Name} --status` (optional `--json`).
3. Run `python3 scripts/check_governance_parity.py` (includes `check_handoff_duplication_pair` — gc7;
   spawn fix cards unless audit-only / `--no-spawn-cards`).
4. When `done/` exists: `python3 scripts/check_lessons_coverage.py --json`.
5. Governance epics: `check_governance_parity.py --line-counts`; optional `--forward-feedback-audit`
   after gel2; optional `--forward-feedback-stale` when closing **`ForwardFeedbackRegistry`** (ff3).
6. Agent runtime smoke: `@` bug card → **Corrective Action** (not Decisions).
7. Write **`## Epic audit (YYYY-MM-DD)`** on anchor (template below); append epic to
   [docs/epics-closed.yaml](../../docs/epics-closed.yaml) via audit turn or
   `resolve_epic_cards.append_closed_epic`.
8. **Do not** reuse closed `epic:` on new cards — new PascalCase epic for follow-ups.
9. **Do not** batch-move to `archived/` on epic audit same turn — run § Archive group when user
   confirms `archive group {Name} complete` (single-epic groups may reuse the epic name, e.g.
   `ForwardFeedbackRegistry`).
10. Emit **`### Epic summary`** in chat — 1–2 paragraphs, outcomes in plain language (§ Epic /
    initiative completion summary); copy into anchor **`## Summary`** when writing **`## Epic audit`**
    same turn. Signature: `governance-epic-completion-summary`.

Quarterly `create_governance_audit_card.py` is optional backstop only (e.g. 90 days without an epic
close — not primary cadence). Signature: `governance-epic-completion-audit`.

**`## Epic audit (YYYY-MM-DD)` template (anchor card):**

```markdown
## Epic audit (YYYY-MM-DD)

- **Epic:** `GovernanceEpicLifecycle`
- **Manifest:** all ## Epic cards rows done / archived / superseded
- **Parity:** `check_governance_parity.py` — _(pass / N issues; spawned …)_
- **Lessons coverage:** _(N/A no done/ | composite X% — per-card C4 …)_
- **Line counts:** _(gc0 — optional for governance epics)_
- **Runtime smoke:** _(agent @ bug card → Corrective Action — pass/fail)_
- **Waivers:** _(KNOWN_DRIFT: … or none)_
- **Spawned fix cards:** _(paths or none)_
- **Closed registry:** appended to docs/epics-closed.yaml
- **Archive group:** _(defer batch to gel3 § Archive group: CardDoneGovernanceLoop2026)_
- **Summary:** _(1–2 sentences — what the epic shipped; plain language; copy from chat ### Epic summary)_
```

### Epic / initiative completion summary (gel4)

On **epic audit** or **archive group complete** turns, add a brief human-readable narrative — distinct
from **`## Epic audit`** / **`## Archive batch`** checklists and Card Done forward feedback.

| Trigger | Chat heading | Anchor persistence |
| ------- | ------------ | ------------------ |
| `close epic {Name}` / `epic complete` | **`### Epic summary`** | **`## Summary`** bullet in **`## Epic audit`** |
| `archive group {Name} complete` | **`### Initiative summary`** | **`## Summary`** bullet in **`## Archive batch`** |

**Placement:** [agent-self-evaluation/SKILL.md](../agent-self-evaluation/SKILL.md) §7 — after Card Done
**`### Top forward feedback`** (when present), before **`### Files used`**. Omit on all other turns.

**Content (max 2 paragraphs):**

- **Sources:** anchor **`## Epic cards`** or **`## Archive group`** manifest; member **Decisions** +
  **Lessons captured**; parity / lessons CLI one-liners when relevant.
- **Write:** outcomes and behavior changes — what agents/users can do now.
- **Do not:** raw path dumps, AC checkbox lists, or duplicate forward-feedback questions.

Signature: `governance-epic-completion-summary`.

### Closed epics registry

SSOT: [docs/epics-closed.yaml](../../docs/epics-closed.yaml) — append on epic audit; never reuse
closed `epic:` on new cards.

| CLI | Purpose |
| --- | ------- |
| `resolve_epic_cards.py --epic X --status` | Active / done / archived counts; `complete` when no active |
| `resolve_epic_cards.py --validate-new X` | Pre-spawn gate — exit 1 when closed |
| `resolve_epic_cards.py --list-closed` | List closed names + dates |
| `resolve_archive_group.py --group X --status` | Active / done / archived counts; `complete` when no active |

Rename examples: `GovernanceEpicLifecycle` → new epic after gel0–gel3; `LessonsCoverageMetric` →
themed follow-up when lc4+ work continues under a fresh name.

### Archive group (gel3 — cross-epic batch)

When a feature spans **multiple epics**, **epic audit** and **batch archive** are separate gates.

| Gate | Trigger | Cards move to `archived/`? |
| ---- | ------- | -------------------------- |
| Epic audit | No active cards for one `epic:` + user confirms | **No** — cards stay in `done/` until archive group batch (gel3) |
| Archive group complete | All manifest rows `done` / archived / superseded + user confirms | **Yes** — batch listed members only |

**Manifest SSOT:** anchor card **`## Archive group: {PascalCaseName}`** table (order, card, epic,
status). Members carry matching **`archiveGroup:`** frontmatter (optional `epic:` between
`assignee` and `dueDate`).

**CardDoneGovernanceLoop2026** (2026-06-27, **archived** 2026-06-27): aK (GovernanceCompact gc8),
aM/aN (LessonsCoverageMetric lc4), aO–aR (GovernanceEpicLifecycle gel0–gel3). Retire group name on
new spawns — anchor `archived/agent-governance-gel3-archive-group-batch-2026-06-27.md`.

**Archive group turn (agent):**

1. Verify manifest — every row `done` / `archived` / `superseded`.
2. User confirms `archive group {Name} complete`.
3. Move `done/{id}.md` → `archived/{id}.md` for **listed members**; keep `status: "done"`.
4. Refresh active card links (`done/` → `archived/`); Signature `kanban-card-stale-dependency-links`.
5. Write **`## Archive batch (YYYY-MM-DD)`** on anchor; retire archive group name for new spawns.
6. Emit **`### Initiative summary`** in chat — 1–2 paragraphs (§ Epic / initiative completion
   summary); copy into anchor **`## Summary`** when writing **`## Archive batch`** same turn.
   Signature: `governance-epic-completion-summary`.

**`## Archive batch (YYYY-MM-DD)` template (anchor card):**

```markdown
## Archive batch (YYYY-MM-DD)

- **Group:** `CardDoneGovernanceLoop2026` — **retired**
- **Manifest:** all ## Archive group rows archived
- **CLI:** `resolve_archive_group.py --group {Name} --status` — N archived, 0 active
- **Moved:** listed members `done/` → `archived/`; `status: "done"` preserved
- **Link refresh:** manifest + active card Context/Decisions (`done/` → `archived/`)
- **Signature:** `governance-archive-group-batch`
- **Summary:** _(1–2 sentences — what the initiative delivered; copy from chat ### Initiative summary)_
```

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
| `--paths` | Prefixes from Product Paths (or Label Paths until ks1) |

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

1. Read QA Review + Feature Areas + Product scope (or legacy Label) + Tests + Docs + Out of Scope
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

### Scope refresh checklist

| Section | When |
| ------- | ---- |
| Feature Areas | Fix touched new product area |
| Product Paths | New/edited product path not on card |
| Product Methods | New symbol (non-test) |
| Tests | New test file or `test_*` |
| Docs | New doc path or § |
| feature-areas.yaml | Durable path/handler for area |

Legacy **Label Paths** / **Label Methods** refresh still applies on open cards until ks2.

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

**Same turn (mandatory for labeled cards):**

1. Frontmatter: `status: done`, `completedAt`, bump `modified`
2. Move `.devtool/features/{id}.md` → `.devtool/features/done/{id}.md`
3. Append `## Lessons captured` + `## Forward-looking feedback` on `done/` path
4. `python3 scripts/build_lessons_index.py` when lessons ran
5. `python3 scripts/build_forward_feedback_index.py` when lessons ran — Signature:
   `forward-feedback-card-done-ingest`; advisory exact-question dedup → `duplicate_of` in yaml
   + stderr; surface lines in chat as **`### Forward feedback dedup`** (non-blocking)
6. `### Top forward feedback` in chat (agent-self-evaluation §7)

**Not Card Done:** user reports Review bugs → stay in **review** with `**QA follow-up**` ([kanban-review-qa.mdc](../../rules/kanban-review-qa.mdc)).

**Maintain (gc8):** new Done-signal phrases → this table + `kanban-card-gates.mdc` §2 Card Done row
only — do not duplicate full trigger lists in scoped `kanban-*-cards.mdc`. Classify fingerprint bump
only when `agent-triage/reference.md` § Classify **rows** change, not trigger-table edits alone.
`` `sig:card-done-agent-move-qa-complete` ``

## Card Done — lessons learned capture

Canonical summary: [SKILL.md § Card Done](SKILL.md#card-done--lessons-learned-capture).

### Artifact update table

| Lesson type | Update |
| ----------- | ------ |
| Area workflow | Matching area skill |
| Hard constraint | Scoped `.mdc` rule |
| User-visible behavior | `docs/` per docs-maintenance |
| New symbols/paths | feature-areas.yaml handlers + Product Methods (or Label Methods until ks2) |
| Cross-cutting failure | agent-self-evaluation/reference.md (**Signature** in rules) |
| Prior-lessons discovery | agent-triage/reference.md § Lessons by area |
| Card Done forward feedback | `## Forward-looking feedback` on done card after Lessons captured — Signature: `card-done-forward-feedback` |
| Card Done forward-feedback index | `build_forward_feedback_index.py` after `build_lessons_index.py` when lessons ran; dedup chat — Signature: `forward-feedback-card-done-ingest` |
| Lessons coverage audit | `check_lessons_coverage.py` (C1–C4); `--strict` for C3 without epic-only match — Signature: `lessons-coverage-strict-consumption` |
| C4 Prior lessons block | No line starting with `**` inside block after header; cite done stems (`YYYY-MM-DD.md`, commit-issue `T` timestamps, drift hash ids) — Signature: `lessons-coverage-c2-c3-audit` |
| GovernanceDriftAlert registry path (lc1 scripts) | Extend `_SCHEMA_INTERNAL_PATHS` in `check_governance_parity.py` — not AGENTS area table columns; sibling spawn cards (`lessons_coverage_lib.py`, hook script, test file) share one fix — Signature: `governance-area-schema-parity-tests`, `lessons-coverage-c2-c3-audit` |
| Handoff duplication pair (gc7) | `check_handoff_duplication_pair`; AGENTS End handoff vs SKILL §7 — ≥3 consecutive `- **Field:**` lines — Signature `governance-gc7-handoff-duplication-pair` |
| Epic-completion audit (gel0) | `resolve_epic_cards.py`; `docs/epics-closed.yaml`; reference § Epic audit — Signature `governance-epic-completion-audit`; epic audit ≠ archive when `archiveGroup:` set; chat **`### Epic summary`** — Signature `governance-epic-completion-summary` |
| Archive group batch (gel3) | `resolve_archive_group.py`; reference § Archive group — Signature `governance-archive-group-batch`; Card Done → `done/` only; chat **`### Initiative summary`** — Signature `governance-epic-completion-summary` |
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
| **References** | yes | Rules, skills, signatures, scripts, governance paths; optional `ff-*` index id |
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

Epic **`DocsGovernanceSplit`** (dg0–dg3) — separate **product contributor docs** from **agent/governance
narrative** currently mixed in `docs/development.md` (~500 lines of Cursor agent workflow). Signature:
`docs-governance-split`.

**Phases:** dg0 schema → dg1 move prose + stub `development.md` → dg2 routing rollout
(AGENTS/skills/rules/README) → dg3 grep + parity verify + gel0 close — **epic closed 2026-06-27**
(all phases in `archived/`). **dg3 gate:**
`python3 scripts/check_governance_parity.py --docs-governance-split` (or
`rg "development.md §" .cursor AGENTS.md docs/ --glob '!docs/forward-feedback-index.yaml'`) → zero
stale § anchors in governance artifacts (Signature: `docs-governance-split`).

### Target tree (post-dg1)

```text
docs/
  development.md                 # product dev only — venv, hooks, pytest, dependencies (~120 lines)
  feature-areas.yaml             # yaml SSOT — path unchanged
  lessons-index.yaml             # generated — path unchanged
  forward-feedback-index.yaml    # generated — path unchanged
  epics-closed.yaml              # registry — path unchanged
  governance/                    # contributor handbook (pointer-first; dg1 creates files)
    README.md
    overview.md
    kanban-workflow.md
    lessons-and-coverage.md
    forward-feedback.md
    feature-areas-parity.md
    audit-and-compaction.md
  ui.md, worldgen.md, …          # product docs — unchanged
.cursor/skills/, .cursor/rules/, AGENTS.md   # canonical enforcement — unchanged SSOT
```

### Audience — who loads what

| Audience | Primary reads | Does not duplicate |
| -------- | ------------- | ------------------ |
| **Human product contributor** | `docs/development.md`, product docs (`ui.md`, …) | Classify tables, kanban card templates, mode-gate matrices |
| **Human governance contributor** | `docs/governance/overview.md` + topic stubs; yaml registries in `docs/` | Full skill/rule prose — follow deep links |
| **Cursor agent** | [AGENTS.md](../../AGENTS.md) → scoped `.cursor/skills/` + `.cursor/rules/` | Long narrative in `docs/governance/` except onboarding skim |
| **CI / scripts** | `docs/*.yaml`, `scripts/check_governance_parity.py`, `scripts/check_lessons_coverage.py` | Markdown handbooks — hardcoded yaml paths stay at `docs/*.yaml` |

### Pointer-first rule (gc1 pattern)

Governance docs under `docs/governance/` are **stubs + deep links** — not second copies of enforcement
text. Canonical detail stays in:

- [AGENTS.md](../../AGENTS.md) — routing entry, Classify quickly summary, Maintaining table
- `.cursor/skills/` and `.cursor/rules/` — lifecycle, gates, Signatures
- `docs/*.yaml` — machine registries (`feature-areas.yaml`, `lessons-index.yaml`, …)

Each governance stub is one-screen: purpose, when to read, link to SSOT. dg2 updates cross-references;
dg3 verifies no stale `development.md` § anchors remain.

### Proposed `docs/governance/` file map (dg1)

| File | One-line purpose |
| ---- | ---------------- |
| `overview.md` | Handbook hub — audience table, load order, links to AGENTS + yaml registries |
| `kanban-workflow.md` | Card scope (Product/Tests/Docs), Cursor mode gates, user prompt verbs — pointers to reference § Kanban card scope and § Cursor mode gates |
| `lessons-and-coverage.md` | Lessons index, feature-area lesson pointers, `artifacts:` schema, Lessons Coverage Metric (C1–C4) |
| `forward-feedback.md` | Forward feedback index — build/query/resolve CLI; ff1–ff3 metrics pointers |
| `feature-areas-parity.md` | Governance area schema (gs0–gs4), on-demand parity check CLI |
| `audit-and-compaction.md` | Periodic governance audit, epic/archive lifecycle pointers, gc0 `--line-counts` baseline |

Merged topics (fewer files, less dg2 churn): kanban subsections share one file; lessons index +
coverage + artifacts share one file; audit + compaction share one file.

### `development.md` section mapping (dg1)

Product sections **stay** in `docs/development.md`. Parent `## Cursor agent workflow` becomes a short
pointer block; `###` subsections move per table.

| Current `development.md` section | dg1 destination | `development.md` stub line (dg1) |
| -------------------------------- | --------------- | -------------------------------- |
| *(intro — venv, UI deps, Amulet)* | **stay** | *(unchanged — product setup)* |
| `## Git hooks` | **stay** | *(unchanged — product hooks)* |
| `## Running checks` | **stay** | *(unchanged — pytest / pre-commit)* |
| `## Cursor agent workflow` (parent) | `docs/governance/overview.md` | Agent and kanban workflow: [docs/governance/overview.md](governance/overview.md) and [AGENTS.md](../AGENTS.md). |
| `### Kanban card scope (Product / Tests / Docs)` | `docs/governance/kanban-workflow.md` | Kanban scope: [kanban-workflow.md](governance/kanban-workflow.md#kanban-card-scope). |
| `### Cursor mode gates (Plan / Inquire / verbs)` | `docs/governance/kanban-workflow.md` | Mode gates: [kanban-workflow.md](governance/kanban-workflow.md#cursor-mode-gates). |
| `### User prompts (agent workflow)` | `docs/governance/kanban-workflow.md` | Prompt verbs: [kanban-workflow.md](governance/kanban-workflow.md#user-prompts). |
| `### Lessons reference index` | `docs/governance/lessons-and-coverage.md` | Lessons index: [lessons-and-coverage.md](governance/lessons-and-coverage.md#lessons-reference-index). |
| `### Forward feedback index` | `docs/governance/forward-feedback.md` | Forward feedback: [forward-feedback.md](governance/forward-feedback.md). |
| `### Lessons Coverage Metric` | `docs/governance/lessons-and-coverage.md` | Coverage metric: [lessons-and-coverage.md](governance/lessons-and-coverage.md#lessons-coverage-metric). |
| `### Feature area lesson pointers (li2)` | `docs/governance/lessons-and-coverage.md` | Lesson pointers: [lessons-and-coverage.md](governance/lessons-and-coverage.md#feature-area-lesson-pointers). |
| `### Governance area schema (gs0)` | `docs/governance/feature-areas-parity.md` | Area schema: [feature-areas-parity.md](governance/feature-areas-parity.md#governance-area-schema). |
| `### Lessons captured artifacts: schema` | `docs/governance/lessons-and-coverage.md` | Artifacts schema: [lessons-and-coverage.md](governance/lessons-and-coverage.md#lessons-captured-artifacts). |
| `### Periodic governance audit` | `docs/governance/audit-and-compaction.md` | Governance audit: [audit-and-compaction.md](governance/audit-and-compaction.md#periodic-governance-audit). |
| `### On-demand parity check` | `docs/governance/feature-areas-parity.md` | Parity CLI: [feature-areas-parity.md](governance/feature-areas-parity.md#on-demand-parity-check). |
| `### Governance compaction (gc0 baseline)` | `docs/governance/audit-and-compaction.md` | Compaction baseline: [audit-and-compaction.md](governance/audit-and-compaction.md#governance-compaction). |
| `## Dependencies` | **stay** | *(unchanged — pyproject extras)* |

### Non-goals (this epic)

- **No moving generated yaml** — `docs/lessons-index.yaml`, `docs/forward-feedback-index.yaml`,
  `docs/feature-areas.yaml`, `docs/epics-closed.yaml` stay at current paths (scripts hardcode `docs/`).
- **No duplicating kanban card templates** — templates remain in this reference and scoped
  `kanban-*.mdc`; governance stubs link here.
- **No `feature-areas.yaml` path change** — deferred to a separate epic if ever needed.
- **dg0–dg2 complete** — schema, prose move, routing rollout done; **dg3** adds automated residual
  grep / parity check (gel0 close on dg0 anchor).

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
