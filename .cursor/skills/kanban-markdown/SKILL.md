---
name: kanban-markdown
description: >-
  Create, read, update, move, and manage kanban board feature files backed by
  markdown with YAML frontmatter. Use when working with kanban boards, task/feature
  tracking, `.devtool/features/` directories, feature files with status/priority
  frontmatter, or any project management tasks involving markdown-based kanban
  workflows. Agent fills ## Decisions after pre-implementation card review (feature cards)
  or ## Corrective Action (bug cards with labels including bug); user writes ## Feature
  Areas on cards; agent resolves to ## Label Paths and ## Label Methods via
  docs/feature-areas.yaml and MUST update that registry after every implementation;
  MUST run ## Prior lessons gate (scripts/resolve_prior_lessons.py) before Decisions/CA;
  MUST mark ## Acceptance Criteria [x] when moving to review; MUST review and update
  docs/ per docs-maintenance (no exceptions). Review QA fixes: append **QA follow-up**
  on card and refresh **Feature Areas** / **Label Paths** / **Label Methods** when scope
  changes (§ User-reported QA fixes). User Done: capture lessons learned (§ Card Done).
  Bug cards: user provides Steps to
  Reproduce, Current/Expected Behavior, Feature Areas, QA Review; agent provides
  Root Cause, Acceptance Criteria, Out of Scope, Label Paths, Label Methods,
  Corrective Action. Inquiry cards: user provides Description and optional Feature
  Areas; agent provides Response and Label Paths + Label Methods when Feature Areas set.
  Agent cards (labels includes agent): user provides Description and Feature Area
  (default Agent Workflow); agent provides Label Paths, Label Methods, Acceptance
  Criteria, and Decisions.
---

# Kanban Markdown

**Canonical task queue for agents.** Use this skill — not [docs/roadmap.md](../../docs/roadmap.md) — for:

- What to work on next (**To Do** column only)
- Moving cards `todo` → `in-progress` → `review` when executing work
- Updating status after implementation (agent stops at **Review**; user moves to **Done**)

`docs/roadmap.md` is legacy reference only; do not add new items there.

## Agent scope (important)

| Column | Agent |
| ------ | ----- |
| **To Do** (`todo`) | **Read** — this is the work queue |
| **In Progress** (`in-progress`) | **Update** — feature/bug/agent/commit-issue: after card review **and** **`## Decisions`** or **`## Corrective Action`**; inquiry: while researching |
| **Review** (`review`) | **Update** — move here when implementation is complete (`in-progress` → `review`); implement **`## QA Review`** when the user asks; **record QA fixes** on the card (§ User-reported QA fixes) |
| **Done** (`done`) | **Do not move** — user moves here after manual app review; when user says **Done**, agent runs **lessons learned capture** only for **`feature` / `bug` / `agent` / `commit-issue`** (§ Card Done). **`inquiry` Done → no lessons.** |
| **Backlog** (`backlog`) | **Ignore** — user-managed; do not list, prioritize, or create cards here unless the user explicitly asks |

Do **not** grep or summarize Backlog cards when the user asks “what should I work on?” or similar.

## How users reference cards

When the user assigns work, resolve the card using this precedence (best first):

| User says | Agent resolves |
| --------- | -------------- |
| File path, e.g. `.devtool/features/render-selection-2026-06-22.md` | Read that file (must be **To Do**, **In Progress**, or **Review** unless user names another column) |
| Card `id` slug, e.g. `render-selection-2026-06-22` | Grep `id: "render-selection-2026-06-22"` under `.devtool/features/` |
| **Title**, e.g. “Render Selection” | Grep To Do cards; match `#` heading |
| **First / next To Do card** | `status: "todo"`, sort by `order`, take first |
| **Continue / finish** + title | Grep `in-progress` or `review` for that card |
| Attached `.md` from `.devtool/features/` | Treat as the named card |

**Recommended user prompts:**

```text
Review .devtool/features/render-selection-2026-06-22.md
```

```text
Review and update .devtool/features/render-selection-2026-06-22.md
```

```text
Kanban: implement render-selection-2026-06-22.
```

```text
Kanban: answer inquiry on my-card-id.
```

**Do not treat as a card assignment:**

| User says | Agent does |
| --------- | ---------- |
| `docs/roadmap.md` | Legacy doc — not the queue |
| Backlog card (unless explicit) | Ignore per § Agent scope |
| Epic only, e.g. “RenderEngine” | Ask which card, or list matching **To Do** cards by title |
| “Move to Done” | **User** action after manual app review — agent stops at **Review** |
| Vague feature description with no card | Ask which To Do card, or offer to create one in **`todo`** |

If multiple To Do cards match, list titles + paths and ask the user to pick one.

### Ask-only vs Agent prompts

Classify the user message **before** any edit. Full table: [kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2.

| Mode | When | User examples |
| ---- | ---- | ------------- |
| **Ask-only** | `review …` without update/implement/spawn; bare `@.devtool/features/…`; no card | `review @foo.md`, `review enforce-ask-only-…` |
| **Agent** | Agent verb + card (path, `id`, or title) | `review and update …`, `update … card`, `spawn cards from …`, `implement …`, `Kanban: answer inquiry on …` |

**Ask-only review** — read card + codebase; report in chat; **do not** edit card body, governance, or product code until the user upgrades the verb.

**Promoted lesson (2026-06-25):** Two gates stack — (1) no card → ask-only (`kanban-no-card-implement`); (2) card named + review-only verb → ask-only (`kanban-prompt-ask-vs-agent`). User upgrades with `review and update`, `update`, `spawn`, or `implement`. Keep **Classify quickly** ↔ triage §1 ↔ `CLASSIFY_ANCHORS` (`review card only`, `agent verb on card`) in sync when changing either gate.

**Feature cards** (`labels: ["feature"]`):

```text
User assigns card (path or title)
  → pre-implementation card review (no code)
  → user resolves clarifications / approves card edits
  → agent resolves ## Feature Areas → ## Label Paths + ## Label Methods (docs/feature-areas.yaml)
  → agent fills ## Decisions on the card
  → todo → in-progress → implement (read Label Methods first; grep only for gaps)
  → staged pytests green
  → agent updates docs/feature-areas.yaml (mandatory)
  → agent reviews and updates docs/ per docs-maintenance (mandatory, no exceptions)
  → agent marks ## Acceptance Criteria [x] for all shipped bullets (mandatory)
  → in-progress → review
  → user runs ## Verify (manual app checks)
  → user adds ## QA Review during review (if any)
  → agent reviews and implements ## QA Review (if any)
  → user reports QA issues in chat/screenshots → agent fixes + records on card (§ User-reported QA fixes)
  → staged pytests green
  → user: review → done
  → user says card is Done → agent captures lessons learned (§ Card Done — lessons learned)
```

**Bug cards** (`labels` includes `bug` — see § Bug cards): use **`## Corrective Action`** instead of **`## Decisions`**; agent also writes **`## Root Cause (current code)`** and **`## Acceptance Criteria`** during card review.

**Inquiry cards** (`labels` includes `inquiry` — see § Inquiry cards): research-only — agent writes **`## Response`**; no code unless the user explicitly asks; move to **Review** when **Response** is complete.

**Agent cards** (`labels` includes `agent` — see § Agent cards): governance / skills / rules / agent workflow — user writes **`## Description`** and **`## Feature Area`**; agent writes **`## Label Paths`**, **`## Label Methods`**, **`## Acceptance Criteria`**, and **`## Decisions`** before `in-progress`.

## Board location

| Path | Role |
| ---- | ---- |
| `.devtool/features/*.md` | Active cards (`backlog`, `todo`, `in-progress`, `review`) |
| `.devtool/features/done/*.md` | Completed cards (`done`) |
| `.devtool/features/archived/*.md` | Archived completed cards — **prior lessons gate** scans with `done/` |

Configurable via VS Code `kanban-markdown.featuresDirectory` (default `.devtool/features`).

## Columns

| status | Column |
| ------ | ------ |
| `backlog` | Backlog |
| `todo` | To Do |
| `in-progress` | In Progress |
| `review` | Review |
| `done` | Done (file in `done/` subfolder) |

**priority:** `critical` | `high` | `medium` | `low`

## Feature Areas (user) vs Label Paths + Label Methods (agent)

Users tag cards with **product areas** they understand. Agents resolve those labels to **repo file paths** and **methods/symbols** before coding — so implementation turns need fewer broad greps.

| Section | Who writes | Content |
| ------- | ---------- | ------- |
| **`## Feature Areas`** | **User** (when creating or editing the card) | Stable labels: `Render Tab`, `Render Preview`, `Paint Brush Panel`, … |
| **`## Feature Area`** | **User** (**agent** cards only) | Single label; default `` `Agent Workflow` `` |
| **`## Label Paths`** | **Agent** (during pre-implementation card review) | Resolved paths from [docs/feature-areas.yaml](../../docs/feature-areas.yaml) plus any new files discovered in review |
| **`## Label Methods`** | **Agent** (same review step, when Feature Areas present) | Functions, methods, Qt slots, and test names the implementation will touch — keyed by path |

**Canonical registry:** [docs/feature-areas.yaml](../../docs/feature-areas.yaml) — maps each label → `paths`, `wiring`, `tests`, `related`, optional `handlers` (stable entry points), `docs`, optional `lesson_signatures` / `lesson_docs` (curated highlights; li2), optional `agents_skill` / `agents_rules` / `lesson_routing_row` (governance routing; **gs0–gs3 complete** — see [docs/development.md](../../docs/development.md) § Governance area schema). **Source of truth** for agent skill/rule routing is yaml — AGENTS.md **Area → skills & rules** table is narrative until a follow-up sync epic (Signature: `governance-area-schema-defer-agents-table`). **Seeded areas:** Render Preview, Agent Workflow, Properties Panel, Feature Area Registry, Palette Registry — verify with `--agents-parity` during card review; do not edit AGENTS table rows when adding governance keys to new areas.

Resolve labels before coding:

```bash
python scripts/resolve_feature_areas.py "Render Preview" "Render Selection"
python scripts/resolve_feature_areas.py --handlers "Open Structures Workflow"
python scripts/resolve_feature_areas.py --lessons "Render Preview"
python scripts/resolve_feature_areas.py --agents-parity "Render Preview"
python scripts/resolve_feature_areas.py --list
```

### Pre-implementation card review (paths + methods)

When **`## Feature Areas`** or an agent card **`## Feature Area`** is present:

1. Resolve paths: `python scripts/resolve_feature_areas.py "<label>" …` (dedupe; include `tests`)
2. Seed methods: `python scripts/resolve_feature_areas.py --handlers "<label>" …` (registry `handlers` only — refine per card)
3. Write draft **`## Label Paths`** and **`## Label Methods`**
4. **Prior lessons gate:** `python3 scripts/resolve_prior_lessons.py --epic "<epic>" "<labels…>" --paths …` — see § Prior lessons gate
5. Read card **AC**, repro; one **surgical grep per path**; finalize **Label Methods**; write **Decisions** / **Corrective Action**

**Label Methods rules:**

- List only symbols this card’s plan implies changing — not whole-file indexes
- Format: `` `path/to/file.py` — `symbol_one`, `symbol_two` `` (one bullet per file)
- Include private handlers (`_on_*`), public API, widget methods, and planned `(new) ClassName` symbols from Corrective Action
- Cap: ≤8 methods per file, ≤20 total unless card is explicitly cross-cutting
- Implementation: open **Label Methods** first; grep only when a symbol is missing or plan shifts

**Unknown label:** ask the user or propose a new registry entry; do not guess file paths or methods.

**No Feature Areas:** surgical/ad-hoc work — grep-first; no Label Methods required on card.

### Example (agent after card review)

```markdown
## Label Paths

- `ui/main_window.py`
- `ui/reload.py`
- `tests/test_main_window.py`

## Label Methods

- `ui/main_window.py` — `MainWindow._on_open_structure`, `MainWindow._restart_editor_for_structure`, `MainWindow._block_if_render_in_progress`
- `ui/reload.py` — `open_structure_in_editor_process`
- `tests/test_main_window.py` — `test_pick_structure_stage_*` (add: open while preview render active)
```

## Bug cards (`labels: ["bug"]`)

When frontmatter is **`labels: ["bug"]`** (inline JSON array — required form for new cards), the card follows the **bug** section split below. Do **not** use **`## Decisions`** on bug cards — use **`## Corrective Action`** instead.

**Frontmatter (required on create):**

```yaml
labels: ["bug"]
```

Do **not** use block-list form (`labels:` / `- bug`).

### Who writes what

| Section | Who | When |
| ------- | --- | ---- |
| **`## Steps to Reproduce`** | **User** | Card creation / before agent pickup |
| **`## Current Behavior`** | **User** | Card creation / before agent pickup |
| **`## Expected Behavior`** | **User** | Card creation / before agent pickup |
| **`## Feature Areas`** | **User** | Card creation / before agent pickup |
| **`## QA Review`** | **User** | During **Review** (follow-up issues found in app) |
| **`## Root Cause (current code)`** | **Agent** | Pre-implementation card review (after reading code) |
| **`## Acceptance Criteria`** | **Agent** | Pre-implementation card review (testable fix bullets) |
| **`## Out of Scope`** | **Agent** | Pre-implementation card review (optional) |
| **`## Label Paths`** | **Agent** | Pre-implementation card review (resolved from Feature Areas) |
| **`## Label Methods`** | **Agent** | Pre-implementation card review (symbols to edit — see § Feature Areas) |
| **`## Corrective Action`** | **Agent** | Pre-implementation card review (concrete fix plan before `in-progress`) |

**Legacy headings:** treat **`## What happens`** as **`## Current Behavior`** on older bug cards; rename when editing the card.

### Recommended bug card section order

1. `# Title` + one-line summary
2. `## Steps to Reproduce` (user)
3. `## Current Behavior` (user)
4. `## Expected Behavior` (user)
5. `## Root Cause (current code)` (agent)
6. `## Acceptance Criteria` (agent)
7. `## Out of Scope` (agent, optional)
8. `## Feature Areas` (user)
9. `## Label Paths` (agent)
10. `## Label Methods` (agent, when Feature Areas present)
11. `## Corrective Action` (agent)
12. `## Verify` (optional — user manual checks)
13. `## QA Review` (user, during review)

### Bug card workflow gates

| Gate | Requirement |
| ---- | ----------- |
| Before `todo` → `in-progress` | User sections present (or user explicitly waives); agent sections filled: **Root Cause**, **Acceptance Criteria**, **Label Paths**, **Label Methods** (when Feature Areas set), **Corrective Action** |
| Before implementation | **`## Corrective Action`** is concrete — not `TBD` or disputed |
| Before `in-progress` → `review` | All **Acceptance Criteria** `[x]`; staged pytests green; `docs/feature-areas.yaml` + `docs/` updated |

Example **Corrective Action** (agent, before coding):

```markdown
## Corrective Action

- Add `_preview_stale` on `MainWindow`; set after successful save paths; clear when preview render finishes.
- `_ensure_preview_render()`: skip cached PNG short-circuit when stale or document has unsaved changes.
- `_on_tab_changed`: call `_ensure_preview_render()` when **Viewer** tab is selected.
- Tests in `tests/test_render_preview.py`; update `docs/ui.md` Viewer section.
```

## Commit-issue cards (`labels` includes `commit-issue`)

When frontmatter `labels` contains **`commit-issue`**, the card was **auto-created** by `scripts/on_pre_commit_failure.sh` after a failed `git commit`. Rule: [kanban-commit-issue-cards.mdc](../../rules/kanban-commit-issue-cards.mdc).

### Who writes what

| Section | Who | When |
| ------- | --- | ---- |
| **`## Problem`** | **Capture script** | On failed commit (hook log excerpt) |
| **`## Failed Tests`** | **Capture script** | On failed commit (pytest test **file** paths) |
| **`## Staged files`** | **Capture script** | On failed commit |
| **`## Root Cause (current code)`** | **Agent** | When user asks to **review** the card |
| **`## Corrective Action`** | **Agent** | When user asks to **review** the card |
| **`## Label Paths`** | **Agent** | Optional during review (from failed tests / staged paths) |
| **`## Label Methods`** | **Agent** | Optional during review (from traceback, test names, staged paths) |

### Reusable pattern? (on review)

After **Root Cause** and **Corrective Action**, ask whether the failure is a **reusable hook/pytest pattern**. If yes:

1. Add a row to [pre-commit-workflow/reference.md](../pre-commit-workflow/reference.md) § Failure patterns ([agent-self-evaluation/SKILL.md](../agent-self-evaluation/SKILL.md) §6f)
2. Cite **Signature** in [testing.mdc](../../rules/testing.mdc) when a hook constraint applies — no duplicate **Fix pattern** prose
3. Note promoted **Signature** in **Corrective Action**

### Workflow

```text
git commit fails
  → scripts/create_commit_issue_card.py writes todo card (labels: commit-issue)
User: review commit-issue card
  → agent reads Problem / Failed Tests / code → Root Cause + Corrective Action (no code yet)
User approves → asks to implement
  → todo → in-progress → fix per Corrective Action → review → user: done
```

### Gates

| Gate | Requirement |
| ---- | ----------- |
| **Review** (user asks) | Agent fills **Root Cause** and **Corrective Action** — **do not implement** until user approves |
| Before `todo` → `in-progress` | User explicitly approved **Corrective Action** and asked to implement |
| Before `in-progress` → `review` | Fix applied; `scripts/pre-commit-pytest.sh` green on staged paths; commit would pass |

Skip card creation: `SKIP_COMMIT_ISSUE_CARD=1 git commit …`

## Agent cards (`labels` includes `agent`)

When frontmatter `labels` contains **`agent`** (case-insensitive), the card is **agent / governance work** — skills, rules, `AGENTS.md`, kanban process, scripts under `scripts/` that support agents. Rule: [kanban-agent-cards.mdc](../../rules/kanban-agent-cards.mdc).

Use **`## Feature Area`** (singular) — one registry label per card. Default when the user omits it: `` `Agent Workflow` ``.

### Who writes what

| Section | Who | When |
| ------- | --- | ---- |
| **`## Description`** | **User** | Card creation / before agent pickup — instructions for the agent |
| **`## Feature Area`** | **User** | Card creation — one backtick-quoted label; default `` `Agent Workflow` `` |
| **`## Label Paths`** | **Agent** | Pre-implementation card review (resolved from Feature Area) |
| **`## Label Methods`** | **Agent** | Pre-implementation card review — scripts, symbols, doc sections |
| **`## Acceptance Criteria`** | **Agent** | Pre-implementation card review (testable bullets) |
| **`## Decisions`** | **Agent** | Pre-implementation card review (concrete plan before `in-progress`) |
| **`## QA Review`** | **User** | During **Review** (optional follow-ups) |

Do **not** use **`## Corrective Action`**, **`## Root Cause (current code)`**, or **`## Response`** on agent cards.

### Label Methods (agent / governance work)

Same bullet format as § Feature Areas (`path` — `symbol`, …). Include what this card will edit:

- **Scripts** — `scripts/foo.py` — `function_name`, `main`
- **Skills / rules** — `.cursor/skills/kanban-markdown/SKILL.md` — `§ Agent cards`; `.cursor/rules/agent-routing.mdc` — lifecycle block
- **Registry docs** — `AGENTS.md` — `### Card types`; `docs/feature-areas.yaml` — `Agent Workflow` entry
- **Tests** — `tests/test_foo.py` — `test_bar`

Cap: ≤8 methods per file, ≤20 total unless the card is explicitly cross-cutting.

### Recommended agent card section order

1. `# Title` + one-line summary (optional)
2. `## Description` (user)
3. `## Feature Area` (user — default `` `Agent Workflow` ``)
4. `## Label Paths` (agent)
5. `## Label Methods` (agent)
6. `## Acceptance Criteria` (agent)
7. `## Decisions` (agent)
8. `## Verify` (optional — user manual checks)
9. `## QA Review` (user, during review)

### Agent card workflow

```text
User creates todo card (labels: agent) with ## Description + ## Feature Area
  → agent pre-implementation card review
  → resolve Feature Area → ## Label Paths + ## Label Methods
  → agent fills ## Acceptance Criteria + ## Decisions
  → todo → in-progress → implement (Python lines ≤ 100 chars)
  → staged pytests green; docs/feature-areas.yaml + docs/ updated when needed
  → mark AC [x] → review → user: done
```

### Gates

| Gate | Requirement |
| ---- | ----------- |
| Before `todo` → `in-progress` | **Description** present; **Feature Area** set or defaulted; agent sections filled: **Label Paths**, **Label Methods**, **Acceptance Criteria**, **Decisions** |
| Before implementation | **Decisions** concrete — not `TBD` |
| Before `in-progress` → `review` | All **Acceptance Criteria** `[x]`; staged pytests green; registry + `docs/` updated when behavior or paths changed |

### Spawn phased agent card series

When the user asks for **`labels: ["agent"]`** cards for a multi-step governance epic (metric, audit, CI):

1. Create one **todo** card per phase under `.devtool/features/` — **never Backlog**.
2. Shared frontmatter: `labels: ["agent"]`, `epic: "{PascalCaseEpic}"` (e.g. `LessonsCoverageMetric`), `order` prefix per series (`lc0`, `lc1`, …).
3. **User sections on every card:** `## Description`, `## Feature Area` (default `` `Agent Workflow` ``).
4. **Agent sections at spawn** (review-ready): `## Label Paths`, `## Label Methods`, `## Acceptance Criteria`, `## Decisions`; optional `## Context` with phase table linking sibling paths.
5. First card `## Context` may list the full series; later cards note **Depends on** / **Blocked by** prior `order`.
6. Implement in `order` sequence unless user re-prioritizes.

**Example epics:** `LessonsCoverageMetric` — lc0 spec (`docs/development.md`), lc1 audit script (`check_lessons_coverage.py`), lc2 C2/C3 heuristics, lc3 CI + drift alerts. `LessonsReferenceIndex` — li0 index builder (`docs/lessons-index.yaml`), li1 `artifacts:` schema, li2 feature-areas pointers, li3 triage routing table. `GovernanceAreaSchema` — gs0 yaml keys spec, gs1 seed areas, gs2 parity script, gs3 pytest + `--agents-parity` (AGENTS table layout deferred). `ArtifactsDocYaml` — ap0 `_normalize_doc_ref` yaml fix, ap1 docs + index refresh.

Example **Description** (user):

```markdown
## Description

Add a kanban label `agent` for governance cards. Agents must keep Python lines ≤ 100
characters on edits. Document the workflow in skills and rules.
```

Example **Feature Area** (user):

```markdown
## Feature Area

- `Agent Workflow`
```

## Inquiry cards (`labels` includes `inquiry`)

When frontmatter `labels` contains **`inquiry`** (case-insensitive), the card is a **research / Q&A** item — not an implementation task. Do **not** use **`## Decisions`**, **`## Corrective Action`**, or **`## Acceptance Criteria`** unless the user later converts the inquiry into a feature or bug card.

### Who writes what

| Section | Who | When |
| ------- | --- | ---- |
| **`## Description`** | **User** | Card creation / before agent pickup |
| **`## Feature Areas`** | **User** | Optional — omit when the question is not about an existing product area |
| **`## Label Paths`** | **Agent** | When **`## Feature Areas`** is present — resolve via `docs/feature-areas.yaml` |
| **`## Label Methods`** | **Agent** | When **`## Feature Areas`** is present — symbols from research + registry `handlers` |
| **`## Response`** | **Agent** | After researching the question (code, docs, registry as needed) |

### Recommended inquiry card section order

1. `# Title` + one-line summary (optional under title)
2. `## Description` (user)
3. `## Feature Areas` (user, optional)
4. `## Label Paths` (agent, when Feature Areas present)
5. `## Label Methods` (agent, when Feature Areas present)
6. `## Response` (agent)

### Inquiry card workflow

```text
User assigns inquiry card (path or title)
  → agent confirms ## Description (ask user if missing)
  → optional: resolve ## Feature Areas → ## Label Paths + ## Label Methods
  → todo → in-progress
  → agent researches (read-only; grep/read docs and code)
  → agent writes ## Response on the card
  → in-progress → review
  → user reads Response; may create new feature/bug cards from suggested follow-ups
  → user asks to spawn / implement recommendations → agent creates feature cards (§ Spawn from inquiry) → `todo`
  → user: review → done
```

### Spawn feature cards from inquiry

When the user asks to **implement recommendations**, **spawn follow-ups**, or **create cards from inquiry** (or equivalent):

1. Read **`## Response`** → **Suggested follow-up cards** (or phased recommendations in the Description).
2. For each recommended **feature** (or **bug** if specified):
   - Create `.devtool/features/{id}.md` with `status: "todo"` — **never Backlog**
   - Set `epic: "{EpicName}"` — PascalCase theme from inquiry title or user (e.g. `DesignFailureMemorySystem`)
   - Set `labels: ["feature"]` for features or `labels: ["bug"]` for bugs
   - `order` — append after existing **todo** cards (`a0`, `a1`, …)
3. **Feature card body** (review-ready — agent fills agent sections at spawn time):

   | Section | Content |
   | ------- | ------- |
   | `# Title` | From recommendation |
   | `## Acceptance Criteria` | Draft bullets `[ ]` from inquiry AC/scope |
   | `## Out of Scope` | From inquiry boundaries |
   | `## Feature Areas` | Backtick-quoted labels; resolve registry if new area needed |
   | `## Label Paths` | Resolved via `docs/feature-areas.yaml` + inquiry evidence |
   | `## Label Methods` | Registry `handlers` + inquiry evidence; refine per card |
   | `## Decisions` | Concrete plan for pre-implementation review |
   | `## Context` | Link to parent inquiry id; phase number if phased |

4. On the **parent inquiry** card:
   - Add **`## Spawned feature cards`** table (path, phase, status)
   - Set matching `epic` on parent when spawning a series
   - Bump `modified`
5. **Do not** move spawned cards to `in-progress` until user assigns implementation (same as any feature card review gate).

**Phased epics:** use consistent `epic` across parent inquiry + all child feature cards; note **Phase N of M** in title or `## Context`; implement in order unless user re-prioritizes. Examples: `DesignFailureMemorySystem` (3 phases); `GovernanceDriftAlerts` (4 phases, phase 4 optional).

**Spawn inquiry from render QA:** when a bug fix reveals **2D vs 3D / worldgen parity** questions (e.g. dual rotation helpers, mask authorship), create a **`labels: ["inquiry"]`** todo card with evidence in **`## Description`** — do not fold research into the closed bug unless user asks. Link from parent bug **Context**.

### Inquiry card gates

| Gate | Requirement |
| ---- | ----------- |
| Before `todo` → `in-progress` | **`## Description`** present (or user explicitly waives) |
| Before `in-progress` → `review` | **`## Response`** is complete — answers the question and includes material usable for future cards |
| Code changes | **None** by default — inquiry cards do not implement features or fixes |
| Pytest / `docs/` / `feature-areas.yaml` | **Not required** for inquiry-only turns (no application code changed) |

### What belongs in `## Response`

Write for a human reader **and** for later card creation:

- **Direct answer** — concise response to the Description
- **Evidence** — key files, docs, or behavior (paths, not long dumps)
- **Suggested follow-up cards** (when applicable) — one subsection per potential card with:
  - Suggested card type (`feature` or `bug`)
  - Proposed title or one-line summary
  - Suggested **`## Feature Areas`** labels
  - Draft acceptance criteria, repro steps, or scope bullets the user can paste into a new card

Example **Response** (agent):

```markdown
## Response

### Answer

Preview PNGs are session-scoped under `output/schematics/_preview/{session}/`. The Viewer tab reuses cached PNGs until save marks them stale or the document has unsaved edits.

### Key paths

- `ui/main_window.py` — `_ensure_preview_render()`, `_preview_stale`
- `ui/render_preview.py` — `cached_preview_gallery_available()`
- `docs/ui.md` — Viewer tab behavior

### Suggested follow-up cards

**Bug: Preview stale after save**
- Feature Areas: `Render Preview`, `Render Tab`
- AC draft: After layer/site save, opening Viewer re-renders when session PNGs are stale.

**Feature: Preview refresh indicator**
- Feature Areas: `Render Preview`
- AC draft: Show loading state on Viewer while background preview render runs.
```

## Label Paths and Label Methods

Repo-relative paths live in **`## Label Paths`**; symbols to edit live in **`## Label Methods`** — both in the card body, **not** in frontmatter `labels`.

Recommended **feature** card sections (in order):

1. `# Title` + user story / summary
2. `## Acceptance Criteria`
3. `## Out of Scope` (optional)
4. `## Feature Areas` (user — product labels; see § Feature Areas)
5. `## Label Paths` (agent — resolved repo paths after card review)
6. `## Label Methods` (agent — when Feature Areas present)
7. `## Decisions` (agent work only — **not** on bug cards; use § Bug cards)
8. `## Verify` (optional — user manual checks only; see § Verify)
9. `## QA Review` (optional — user fills during review; see § QA Review)

For **bug** cards, use the section order in § Bug cards instead. For **inquiry** cards, use § Inquiry cards. For **agent** cards, use § Agent cards.

| Role | Example line |
| ---- | ------------- |
| Primary code | `` `ui/widgets/preview_panel.py` `` |
| Wiring | `` `ui/main_window.py` `` |
| Tests | `` `tests/test_render_preview.py` `` |
| Package | `` `renderers/registry.py` `` |

**Agents picking up a To Do card:**

1. Read **`## Feature Areas`** (user labels) and resolve via [docs/feature-areas.yaml](../../docs/feature-areas.yaml)
2. Write or refresh **`## Label Paths`** and **`## Label Methods`** on the card before `in-progress` (paths deduped; methods scoped to Corrective Action / Decisions)
3. At implementation: jump to symbols in **Label Methods** first; grep only for gaps
4. Map paths to tests via [targeted-testing](../targeted-testing/SKILL.md) or `scripts/pre-commit-pytest.sh`
5. If **Feature Areas**, **Label Paths**, and **Label Methods** are all missing, fall back to [repo-map](../repo-map/SKILL.md) — do not invent paths
6. Ignore frontmatter `labels` for navigation (legacy badge values like `["ui"]` may remain)

**When creating or updating cards (user):**

- **Feature cards** (`labels: ["feature"]`): add **`## Feature Areas`** with 1–5 backtick-quoted labels; optional **`## Acceptance Criteria`** if you write AC yourself (otherwise agent fills during review)
- **Bug cards** (`labels: ["bug"]`): provide **`## Steps to Reproduce`**, **`## Current Behavior`**, **`## Expected Behavior`**, **`## Feature Areas`**; leave agent sections empty
- **Inquiry cards** (`labels: ["inquiry"]`): provide **`## Description`**; **`## Feature Areas`** optional; leave **`## Response`** for the agent
- **Agent cards** (`labels: ["agent"]`): provide **`## Description`** and **`## Feature Area`** (default `` `Agent Workflow` ``); leave agent sections empty
- Leave **`## Label Paths`**, **`## Label Methods`**, **`## Root Cause (current code)`**, **`## Corrective Action`** (bugs), **`## Decisions`** (features and agent cards), or **`## Response`** (inquiries) for the agent
- Set frontmatter `labels: ["bug"]`, `labels: ["inquiry"]`, or `labels: ["agent"]` for typed cards (board badge)
- Optional sections: `## Verify` (user manual checks only — no pytest lines), `## QA Review` (user fills during review), `## Out of Scope` (agent may add on bugs)
- **`## Decisions`** / **`## Corrective Action`** — agent fills after pre-implementation card review; not optional once review is complete

**When creating or updating cards (agent after review):**

- Add **`## Label Paths`** with resolved repo paths (2–10 bullets); include test paths when known
- Add **`## Label Methods`** when **`## Feature Areas`** is set (path-keyed symbol lists; see § Feature Areas)
- Paths: repo root, forward slashes, no leading `/`

Example body (user creates card):

```markdown
## Feature Areas

- `Render Tab`
- `Render Preview`
- `Render Selection`
```

Example body (agent after card review):

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

## Verify

Cards may include **`## Verify`** for **user** manual checks (app behavior, visual review, etc.). The user may append verify bullets over time.

**Agent responsibility (always — not written on the card):**

- **Feature and bug cards:** run staged pytest before moving to **Review**:
  ```bash
  scripts/pre-commit-pytest.sh
  ```
  on files staged for the change (same scope as the pre-commit hook). See [targeted-testing](../targeted-testing/SKILL.md) and [pre-commit-workflow](../pre-commit-workflow/SKILL.md).
- **Inquiry cards:** no pytest gate — research-only unless the user explicitly requests code changes on the same card.
- Do **not** add “run staged pytests” (or similar) to **`## Verify`** when creating or editing cards — that is implicit agent work.
- During **pre-implementation card review**, suggest removing pytest lines from **`## Verify`** if present on legacy cards.

**Before `in-progress` → `review`:** staged pytests green **and** any card **`## Verify`** items are for the **user** to run after handoff (manual app review), not blockers unless the card says otherwise.

## Decisions

**Feature cards only.** Bug cards use **`## Corrective Action`** (see § Bug cards).

**Agent responsibility.** Record implementation choices in **`## Decisions`** on the card after **pre-implementation card review** is complete and before moving `todo` → `in-progress`.

**Typical content:** UI placement, data flow, file/API choices, what to reuse vs add, edge-case handling, and anything that locks scope before coding.

**When to write:**

1. Finish **pre-implementation card review** (read card, check codebase, report clarifications/improvements to user)
2. Resolve open clarifications with the user (or get explicit approval to proceed)
3. **Write or update `## Decisions`** on the card — concrete bullets the implementation will follow
4. Bump `modified`, then move `todo` → `in-progress`

**Do not** start application code while **`## Decisions`** is empty, placeholder (e.g. `TBD by AI`), or still disputed.

**Do not** put acceptance criteria, verify steps, or QA items in **`## Decisions`** or **`## Corrective Action`** — those have their own sections.

## Corrective Action

**Bug cards only.** Feature cards use **`## Decisions`** (see § Decisions).

**Agent responsibility.** After pre-implementation card review, write **`## Corrective Action`** with concrete fix steps (files, signals, tests, docs) before moving `todo` → `in-progress`.

**Typical content:** code paths to change, new state/flags, test files, doc updates, and edge cases the fix must handle.

**Do not** start application code while **`## Corrective Action`** is empty, placeholder (e.g. `TBD by AI`), or still disputed.

Pair with **`## Root Cause (current code)`** — root cause explains *why* it breaks; corrective action states *what* to change.

Example (after card review, before coding):

```markdown
## Decisions

- Group dropdown in `PreviewPanel` toolbar row; hidden when only one group exists.
- Per-Y PNGs under `output/schematics/_preview/{session}/`; filename pattern `Structure_{group}_{y}.png`.
- Thumbnail strip below toolbar; next/previous buttons navigate the same image list.
- Reuse `RenderWorker` + save-first pattern from render-selection card.
```

## Acceptance Criteria

**Feature and bug cards only.** Inquiry cards do not use acceptance criteria (see § Inquiry cards).

**Hard constraint:** before moving `in-progress` → `review`, the agent **MUST** mark every **`## Acceptance Criteria`** bullet **`[x]`** that the implementation satisfies.

**When to check off:**

1. Implementation complete and staged pytests green
2. Walk each AC bullet — if shipped behavior matches, change `- [ ]` → `- [x]` (or fix legacy `- []` → `- [x]`)
3. Bump `modified` on the card in the same edit as the status change to `review`

**Rules:**

| Rule | Detail |
| ---- | ------ |
| **Format** | Use `- [x]` / `- [ ]` (checkbox + space). Not `- []`. |
| **All met** | Every AC bullet must be `[x]` before **Review** unless user explicitly deferred one |
| **Partial / deferred** | Leave `[ ]`, note in handoff, and get user agreement — do not move to **Review** claiming done |
| **QA Review** | If QA work completes an AC that was left unchecked, check it off when implementing QA |
| **Out of scope** | Do not check off bullets moved to **`## Out of Scope`** — remove or rewrite AC instead |

**Do not** move to **Review** or end an implementation turn with open AC bullets that were actually delivered.

Example (before `in-progress` → `review`):

```markdown
## Acceptance Criteria

- [x] Demonstrate the render dropdown includes "Site Facades"
- [x] Demonstrate the in-app render displays each Direction as an individual PNG.
- [x] Demonstrate the PNG are shown as thumbnails
```

## QA Review

Cards may include **`## QA Review`** for follow-up fixes and polish found during **Review**. The **user** populates this section while testing the app — agents do **not** add items here unless the user asks.

**Typical content:** bug fixes, UX tweaks, missing edge cases, test gaps, copy changes — anything discovered after the initial implementation lands in **Review**.

**Agent responsibility when the user asks to implement QA Review** (or assigns a **Review** card with open items in this section):

1. Read the full card — especially **`## QA Review`**, **`## Feature Areas`**, **`## Label Paths`**, **`## Label Methods`**, and **`## Out of Scope`**
2. **Pre-QA review** — confirm each item is clear and in scope; ask the user about ambiguities before coding
3. Implement all open **`## QA Review`** bullets (or the subset the user names)
4. Run `scripts/pre-commit-pytest.sh` on staged paths — same gate as before **Review**
5. Mark implemented bullets done (`[x]`) and bump `modified`
6. Leave `status: "review"` — the **user** moves to **Done** after they accept the fixes

**Do not** move a card to **Done** while **`## QA Review`** has unchecked items — unless the user explicitly says to defer or drop them.

**Do not** add pytest or other implicit agent checklist items to **`## QA Review`** — those belong in agent workflow (see § Verify).

**Before `review` → `done`:** user manual **`## Verify`** checks complete **and** all **`## QA Review`** implemented (or explicitly waived by the user). Agents implement QA items; only the **user** performs the final move to **Done**.

**Spawn bug cards from QA Review** (when user asks to “note bugs” / “create bug cards” without implementing in place):

1. Add **`## QA Review`** bullets on the parent card — distinguish **bugs** (spawn `labels: ["bug"]` cards) vs **deferred scope** (future feature card; link only).
2. Create `.devtool/features/{id}.md` per bug with user sections filled from QA evidence; agent fills **Root Cause**, **Acceptance Criteria**, **Label Paths**, **Label Methods**, **Corrective Action** at spawn time.
3. Add **`## Spawned bug cards`** table on the parent linking paths + one-line summary.
4. Leave parent `status: "review"` until user moves **Done** — open QA bullets for unfixed bugs are expected when work is deferred to child cards.
5. **Deferred scope** (not bugs) → spawn a **feature** card (e.g. C4 attachables after C3 QA); link from parent **`## Spawned feature cards`** and mark QA deferral bullets `[x]` with the new path.
6. **Bug queue order** — set frontmatter `order` (`a0`, `a1`, …) on spawned bug cards in implementation sequence; keep `labels: ["bug"]`; feature follow-ups append after bugs. Record the ordered table on the parent card **`## Spawned bug cards`** (`#`, `order`, `Label` columns).

Example body (user adds during review):

```markdown
## QA Review

- [ ] Preview dropdown should disable while render is in progress
- [ ] Caption text should not show full filesystem path
```

After agent implements:

```markdown
## QA Review

- [x] Preview dropdown should disable while render is in progress
- [x] Caption text should not show full filesystem path
```

## User-reported QA fixes (Review)

During **Review**, the user may report follow-up issues via chat, screenshots, or **`## QA Review`** — not only pre-written card bullets.

**When the user reports a QA issue and asks you to fix it** (or you fix it in the same turn):

1. **Implement** the fix (same pytest/docs gates as initial implementation when code changes).
2. **Record on the card** in the same turn — **mandatory**; do not rely on chat history alone.
3. **Refresh card labels** when the fix touches scope not already on the card (same turn):
   - **`## Feature Areas`** — **append** a product-area label when the fix crosses into a new area (e.g. card had `Render Preview` only but fix also touched `Sprite Baker`). Resolve via `docs/feature-areas.yaml`; do not remove user labels.
   - **`## Label Paths`** — **append** any new or previously omitted repo paths edited or added (files only; dedupe).
   - **`## Label Methods`** — **append** new symbols touched (`path` — `symbol`, …); refine wrong symbols; cap per § Feature Areas.
   - When new paths/symbols are **stable** for the area, also update **`docs/feature-areas.yaml`** (`paths`, `handlers`, `tests`) per implementation gates.
4. Bump card `modified`.

**Where to record** (append dated bullets; do not overwrite shipped **Corrective Action** / **Decisions**):

| Card type | Record under |
| --------- | ------------ |
| `bug` | **`## Corrective Action`** — `**QA follow-up (YYYY-MM-DD):**` symptom → fix → test/doc pointer |
| feature (default) | **`## Decisions`** — same `**QA follow-up**` format |
| `agent` | **`## Decisions`** — same format |

**Optional:** mirror fixed items into **`## QA Review`** as `[x]` bullets when that section exists.

**Example** (bug card):

```markdown
## Corrective Action

- Extend partial face occlusion …

**QA follow-up (2026-06-25):** Black slab tops — 2D half-mask bakes on orbit quads → `_resolve_orbit_slab_face_texture` + `test_orbit_slab_face_textures_are_opaque`.

**QA follow-up (2026-06-25):** Solid face hole above bottom slab → `_collect_solid_slab_neighbor_strip_faces` in `helpers/orbit_greedy_mesh.py` + `test_solid_emits_upper_strip_face_toward_bottom_slab`. **Labels:** appended `helpers/orbit_greedy_mesh.py` + `build_orbit_greedy_mesh_from_context` to **Label Paths** / **Label Methods**.
```

**Label refresh checklist** (after each QA fix that changes code):

| Section | When to update |
| ------- | -------------- |
| **`## Feature Areas`** | Fix touched a product area not already listed |
| **`## Label Paths`** | Fix edited/added a path not on the card |
| **`## Label Methods`** | Fix touched a symbol or test name not on the card |
| **`docs/feature-areas.yaml`** | New path/handler is durable for that area (same gate as initial implementation) |

Mention label updates in the **`**QA follow-up**`** bullet when paths/methods changed (see example above).

**Do not** skip card updates because the fix was "small" or "surgical" — the card is the audit trail.

## Card Done — lessons learned capture

The **user** moves cards to **Done** (`done/{id}.md`). When the user says the card is **done**, **closed**, **move to Done**, or equivalent **after** accepting Review:

**Label scope (mandatory):**

| `labels` | Lessons capture |
| -------- | --------------- |
| `feature`, `bug`, `agent`, `commit-issue` | **Run** this section — [kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) |
| `inquiry` | **Do not run** — close inquiry only; no skill/rule/doc updates for Card Done |

**Agent must run lessons learned capture in that turn** for in-scope labels (even if no code changes in that turn):

1. **Read** the full card — original **Corrective Action** / **Decisions**, all **`**QA follow-up**`** bullets, **Feature Areas**, **Context**.
2. **Distill** durable lessons (symptom → root cause → fix pattern → tests) — not a copy-paste of the whole card.
3. **Update governance artifacts** so future implementations do not repeat the mistake:

| Lesson type | Update (same turn) |
| ----------- | ------------------ |
| Area workflow (UI, render, worldgen, …) | Matching **area skill** (e.g. `ui-change/SKILL.md` § lessons learned) |
| Hard constraint / gate | Matching **scoped `.mdc` rule** (different file from the skill) |
| User-visible behavior | **`docs/`** per [docs-maintenance](../docs-maintenance/SKILL.md) — e.g. `docs/render-types.md` lessons table |
| New symbols / paths | **`docs/feature-areas.yaml`** `handlers:` + card **Label Methods** if missing |
| Registry / palette policy | **`registries/`** + docs as needed |
| Cross-cutting failure | [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) § Common failure patterns (**Signature** only in rules) |
| Agent prior-lessons discovery (kanban + Feature Areas) | [agent-triage/reference.md](../agent-triage/reference.md) § **Lessons by area** — add a row when a Feature Area gains a promoted Signature; keep ≤15 rows (exhaustive list stays in `docs/lessons-index.yaml`) |

4. **Minimum:** edit **≥1 skill** and **≥1 rule** (different learnings) — same bar as implementation turns ([agent-self-evaluation](../agent-self-evaluation/SKILL.md) §6).
5. **Card** — add **`## Lessons captured (YYYY-MM-DD)`** with links to updated skill/rule/doc paths (user may already have moved file to `done/` — edit `done/{id}.md` if present, else active card).

   **Optional structured tail** — one `artifacts:` sub-bullet per lesson (comma-separated). Parsers prefer this over **Governance** link heuristics; see [docs/development.md](../../docs/development.md) § Lessons captured `artifacts:` schema.

   ```markdown
   - **Symptom:** …
   - **Fix:** …
     - artifacts: skill:project-context, rule:testing.mdc#orbit-animated-texture-strip, doc:render-types.md, sig:orbit-animated-texture-strip, test:tests/test_block_texture_load.py
   ```

   Prefixes: `skill:`, `rule:`, `doc:`, `sig:`, `test:` — `rule:` may include `#signature` anchor; `sig:` feeds the lessons index Signature list. For registry YAML under `docs/`, use an explicit extension on `doc:` (e.g. `doc:lessons-index.yaml`, not `doc:lessons-index`); extensionless registry stems are skipped by the parser.

6. **Index** — run `python3 scripts/build_lessons_index.py` so `docs/lessons-index.yaml` stays current (or `--check` before commit when index is staged). When the lesson applies to a **Feature Area**, curate `lesson_signatures` / `lesson_docs` in `docs/feature-areas.yaml` (manual first; `build_lessons_index.py --sync-registry` dry-run suggests diffs — trim to ≤8 / ≤5 before `--write`). **Commit-issue** cards with `artifacts:` → index picks up `done/{id}.md` on rebuild.
7. **Handoff** — `Skills updated:` / `Rules updated:` must list paths; `Docs:` lists lesson doc updates.

**Do not** move the card to **Done** for the user. **Do not** skip lessons capture because AC were already `[x]` — QA follow-ups are the primary source.

**If user says Done but QA follow-ups are open:** ask whether to defer, spawn child cards, or waive before capturing lessons.

## Card label gate (before any work)

Read frontmatter `labels` on every assigned card **before** pre-implementation review or inquiry research.

| `labels` | Valid? | Action |
| -------- | ------ | ------ |
| `["feature"]` | yes | Feature workflow — [kanban-feature-cards.mdc](../../rules/kanban-feature-cards.mdc) |
| `["bug"]` | yes | Bug workflow |
| `["agent"]` | yes | Agent workflow |
| `["inquiry"]` | yes | Inquiry workflow — **no** Card Done lessons |
| `["commit-issue"]` | yes | Commit-issue workflow |
| missing, `[]`, or unknown | **no** | **Stop** — inform user a valid label is required ([kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc)) |

**Spawn / create cards** with explicit labels — use `labels: ["feature"]` for features (not `labels: []`).

## Reading the board

**Default for agents:** To Do column only.

1. `Grep` for `status: "todo"` under `.devtool/features/`
2. Sort matches by `order` (lexicographic fractional index)
3. Read each card’s type (`labels`: **`feature`** / **bug** / **inquiry** / **agent** / **commit-issue**), **`## Feature Areas`** or **`## Feature Area`**, **`## Label Paths`**, **`## Label Methods`**, then other sections
4. **Label gate** — invalid/missing `labels` → stop; do not implement
5. **Feature / bug / agent / commit-issue:** run **pre-implementation card review** (see below) — do **not** implement yet
6. **Inquiry:** run **inquiry card review** (see § Inquiry cards) — research and **`## Response`** only
7. After review, move `todo` → `in-progress` and work the card (implement for feature/bug/agent; research for inquiry)

**Governance lessons queue (`ArtifactsDocYaml`, `LessonsCoverageMetric`, `GovernanceAreaSchema`):** read **To Do** and **Backlog** when the user assigns an epic name, asks for cross-epic order, or re-prioritizes governance work. Sort matching cards by frontmatter `order` (`a0`–`a9` for the current ten-card queue); phase ids (`ap0`, `lc0`, `gs0`, …) live in **Context** tables, not in `order`.

Only read other **Backlog** cards when the user explicitly asks about backlog cards.

For a card already in progress, grep `status: "in-progress"` or `status: "review"` if the user names that card or asks to continue/finish it. For **Review** cards, also read **`## QA Review`** — the user may assign implementation of those items next.

## Pre-implementation card review (required)

**Feature, bug, and agent cards.** Inquiry cards use § Inquiry cards instead. **`commit-issue`:** run § Prior lessons gate during **review** (with **Problem** / **Failed Tests** paths) before **Root Cause** / **Corrective Action**.

**Before any code changes**, review the To Do card for clarifications and improvements. **Implementation is not allowed** until this step is complete.

1. Read the full card — determine **bug** (`labels` includes `bug`) vs **feature** / **agent** card
2. **Bug cards:** confirm user sections (**Steps to Reproduce**, **Current Behavior**, **Expected Behavior**, **Feature Areas**); ask user to fill gaps
3. **Feature / agent cards:** read acceptance criteria, feature areas, out of scope, verify
4. **Resolve `## Feature Areas`** (or agent **`## Feature Area`**) via [docs/feature-areas.yaml](../../docs/feature-areas.yaml) → write **`## Label Paths`** and **`## Label Methods`**
5. **Prior lessons gate** (§ below) — mandatory before **Decisions** / **Corrective Action**
6. **Check against the codebase** — use Label Methods targets; one surgical grep per path; document **`## Root Cause (current code)`** (bugs / commit-issue review)
7. **Bug / commit-issue cards:** write **`## Acceptance Criteria`** (testable), optional **`## Out of Scope`**, and **`## Corrective Action`**
8. **Report to the user:**
   - **Clarifications** — ambiguities, missing scope, or criteria that need a user answer
   - **Improvements** — suggested edits to the card (wording, scope, feature areas)
   - **Stale links** — when **Context** / **Decisions** cite sibling cards, rewrite paths to `archived/` or `done/` and mark dependency **done** vs open (Signature: `kanban-card-stale-dependency-links`)
9. **Resolve before implementing:**
   - Apply agreed card improvements to the `.md` file (bump `modified`)
   - Get explicit user answers for clarifications, or explicit user approval to proceed when none remain
   - **Feature / agent cards:** write **`## Decisions`** (see § Decisions)
   - **Bug / commit-issue cards:** write **`## Corrective Action`**
10. **Then** move the card `todo` → `in-progress` and start implementation

**Do not** move to **In Progress**, edit application code, or run implementation work while clarifications are open or card improvements are still pending user agreement.

If the user only asked to review the card (no implementation), stay in **To Do** and do not move the card.

## Prior lessons gate (pre-implementation)

**Mandatory** after **Label Paths** / **Label Methods** are drafted and **before** **Decisions** or **Corrective Action**. Rule: [kanban-prior-lessons-gate.mdc](../../rules/kanban-prior-lessons-gate.mdc).

Bridge **Card Done** lessons (in **`done/`** or **`archived/`**) and **commit-issue** failures into the current card plan.

**Read order:** (1) `docs/lessons-index.yaml` area block + [agent-triage/reference.md](../agent-triage/reference.md) § **Lessons by area**, (2) optional `resolve_feature_areas.py --lessons` and `--agents-parity` when area has `agents_skill` (gs3), (3) `resolve_prior_lessons.py`, (4) full done card only when still ambiguous.

### 1. Index + routing table

Skim **`docs/lessons-index.yaml`** for each resolved area label and the matching row in [agent-triage/reference.md](../agent-triage/reference.md) § **Lessons by area** before broad done-card grep.

Optional registry pointers:

```bash
python3 scripts/resolve_feature_areas.py --lessons "Render Preview"
python3 scripts/resolve_feature_areas.py --agents-parity "Render Preview"
```

### 2. Run the resolver

```bash
python3 scripts/resolve_prior_lessons.py --epic "RenderEngine" "Render Preview" \
  --paths helpers/orbit_face_textures.py
```

| Argument | Source on card |
| -------- | -------------- |
| `--epic` | Frontmatter `epic` (omit when unset) |
| Positional labels | **`## Feature Areas`** or agent **`## Feature Area`** |
| `--paths` | Prefixes from draft **`## Label Paths`** (optional) |

### 3. Read matched artifacts (when index + resolver insufficient)

| Resolver section | Agent action |
| ---------------- | ------------ |
| **Registry lesson pointers** | Grep listed **Signatures** in reference tables; skim **`lesson_docs`** — no need to open done cards for highlights |
| **Done and archived cards — Lessons captured** | Read full `done/{id}.md` or `archived/{id}.md` when index + resolver are still ambiguous |
| **Open commit-issue cards** | Read **Problem** / **Failed Tests**; grep **Signatures** in pre-commit-workflow + agent-self-evaluation `reference.md` |
| **Feature area docs** | Skim listed `docs/` before **Decisions** |
| **Grep Signatures** | When symptoms match [agent-triage/reference.md](../agent-triage/reference.md) § Failure pattern routing |

Load **area skills & rules** from [AGENTS.md](../../AGENTS.md) § Area → skills & rules.

### 4. Record on the card

Under **Decisions** (feature/agent) or **Corrective Action** (bug/commit-issue):

`**Prior lessons (YYYY-MM-DD):**` — done/archived card path or **Signature**; one bullet per lesson (or `none`).

**Skip:** inquiry research-only; surgical ad-hoc fixes without a card (use triage §1b on failures only).

## File format

Every feature file:

```markdown
---
id: "my-feature-2026-02-20"
status: "backlog"
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

Description and acceptance criteria.

## Label Paths

- `ui/widgets/example_panel.py`
- `tests/test_example_panel.py`
```

**Serialization rules** (extension parser is strict):

- String fields: always `"double-quoted"`
- Nullable fields (`assignee`, `dueDate`, `completedAt`): bare `null` when unset
- `labels`: **`["feature"]`** for feature cards; **`["bug"]`** for bugs; **`["inquiry"]`**; **`["agent"]`**; **`["commit-issue"]`** — inline JSON array on one line (**not** `labels: []` or block-list)
- Order: `"double-quoted"` fractional index
- Field order: `id`, `status`, `priority`, `assignee`, `dueDate`, `created`, `modified`, `completedAt`, `labels`, `order`

**Existing cards** may include optional `epic: null` between `assignee` and `dueDate`. **Use `epic`** when spawning a series from an inquiry (e.g. `epic: "DesignFailureMemorySystem"`). Preserve field position when editing.

## Fractional index ordering

When **creating** a card in a column:

- Empty column → `"a0"`
- Append after last item → increment trailing char: `"a0"` → `"a1"` … `"a9"` → `"aA"` (base-62: `0-9`, `A-Z`, `a-z`)

Drag-and-drop reordering is handled by the extension; agents only need append logic for new cards.

**Multi-epic governance queue:** when a phased series spans epics (`ArtifactsDocYaml` + `LessonsCoverageMetric` + `GovernanceAreaSchema`), use contiguous fractional `order` values in **To Do** (`a0`…`a9`) so lexicographic sort matches cross-epic implementation order. Keep phase labels (`ap0`, `lc0`, `gs0`) in **Context** tables only — not in `order`.

## Creating features

**Do not create cards in Backlog** unless the user explicitly asks.

When the user requests a new tracked item:

1. Ask which column, or default to **`todo`** if they want the agent to pick it up
2. **ID:** lowercase title → keep `a-z 0-9 - space` → spaces to `-` → collapse/trim hyphens → truncate 50 chars → append `-YYYY-MM-DD` (or `feature-YYYY-MM-DD` if empty)
3. **Timestamps:** `created` and `modified` = now (ISO 8601); `order` = after last in target column
4. **Body:**
   - **Feature:** `# Title`, optional user AC, **`## Feature Areas`**; agent fills **Label Paths**, **Label Methods**, **Decisions**
   - **Bug:** `# Title`, user **Steps to Reproduce** / **Current Behavior** / **Expected Behavior** / **Feature Areas**; `labels: ["bug"]`; agent fills **Root Cause**, **AC**, **Label Paths**, **Label Methods**, **Corrective Action**
   - **Inquiry:** `# Title`, user **`## Description`**; optional **`## Feature Areas`**; `labels: ["inquiry"]`; agent fills **Label Paths**, **Label Methods** (if areas set), and **Response**
   - **Agent:** `# Title`, user **`## Description`** + **`## Feature Area`** (default `Agent Workflow`); `labels: ["agent"]`; agent fills **Label Paths**, **Label Methods**, **Acceptance Criteria**, **Decisions**
   - Optional `## Verify` (user manual checks only — no pytest lines)
5. **Done on create:** set `completedAt`, write under `done/`

## Updating features

- Always bump `modified`
- Never change `id` or `created`
- Preserve exact serialization format

## Moving features

Update `status` and `modified`. File stays in `.devtool/features/` until moved to **Done**.

**Agent completes implementation** (`in-progress` → `review`) — **feature, bug, and agent cards**:

- Run `scripts/pre-commit-pytest.sh` on staged paths (agent verify — see § Verify)
- **Update [docs/feature-areas.yaml](../../docs/feature-areas.yaml)** — mandatory (see § Feature area registry)
- **Review and update `docs/`** — mandatory per [docs-maintenance](../docs-maintenance/SKILL.md) (no exceptions)
- **Mark all satisfied `## Acceptance Criteria` bullets `[x]`** — mandatory (see § Acceptance Criteria)
- Set `status: "review"`
- Bump `modified`
- Leave `completedAt: null`
- File remains in `.devtool/features/{id}.md`

**Agent completes inquiry** (`in-progress` → `review`):

- **`## Response`** written on the card (see § Inquiry cards)
- **`## Label Paths`** and **`## Label Methods`** written when **`## Feature Areas`** was provided
- No pytest / docs / registry updates unless application code also changed
- Set `status: "review"`; bump `modified`

**User accepts after manual app review** (`review` → `done`) — **user only**, not the agent:

- All **`## QA Review`** bullets checked or explicitly waived
- Set `completedAt` to now
- Move `{id}.md` → `done/{id}.md`

**From `done` back to active** (user only):

- Set `completedAt` to `null`
- Move `done/{id}.md` → `{id}.md`

## Periodic AGENTS.md governance audit

**Cadence:** quarterly (suggested) or after a large agent/kanban governance epic. Complements in-band [agent-consistency.mdc](../../rules/agent-consistency.mdc) + [Consistency matrix](../agent-triage/reference.md).

**Template card:** run `python3 scripts/create_governance_audit_card.py` (writes `.devtool/features/agents-md-governance-audit-YYYY-MM-DD.md` with a fresh checklist). Archive completed audits under `done/`; do not hunt in `archived/`.

### Who does what

| Step | Who |
| ---- | --- |
| Create **todo** audit card | **User** — `python3 scripts/create_governance_audit_card.py` (or `--date YYYY-MM-DD`, `--force` to reset) |
| Compare artifacts, fill **## Audit findings** | **Agent** (read-only — no fixes unless user asks) |
| Spawn fix cards from drift bullets | **User** assigns follow-up feature/bug cards |
| Move audit → **done** | **User** after findings addressed or waived |

### Audit checklist (grep / compare — do not paste full prose)

- [ ] **Routing:** [AGENTS.md](../../AGENTS.md) Every turn (steps 1–5, 1b) ↔ [agent-triage/SKILL.md](../agent-triage/SKILL.md) §1/§1b ↔ [agent-routing.mdc](../../rules/agent-routing.mdc) lifecycle
- [ ] **Classify:** AGENTS.md Classify quickly ↔ agent-triage §1 table
- [ ] **Card types:** AGENTS.md card types table ↔ each `kanban-*.mdc` ↔ [kanban-markdown](SKILL.md) § Bug / Inquiry / Commit-issue / Agent cards
- [ ] **Handoff:** AGENTS.md End handoff ↔ [agent-self-evaluation/SKILL.md](../agent-self-evaluation/SKILL.md) §7 ↔ [agent-self-evaluation.mdc](../../rules/agent-self-evaluation.mdc)
- [ ] **Area table:** AGENTS.md area → skills & rules includes current scoped rules (`agent-consistency`, `kanban-*`, …) and **Agent Workflow** yaml skills (`agent-triage`, `agent-self-evaluation`, `kanban-markdown`, `pre-commit-workflow`, …) on Agent/Kanban rows
- [ ] **Failure patterns:** Signatures in rules/triage exist in [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) or [pre-commit-workflow/reference.md](../pre-commit-workflow/reference.md); [Consistency matrix](../agent-triage/reference.md) rows still accurate
- [ ] **Docs:** [docs/development.md](../../docs/development.md) Cursor agent workflow ↔ AGENTS.md + consistency links
- [ ] **Kanban cards:** cards with **`## Feature Areas`** also have **`## Label Paths`** + **`## Label Methods`** before `in-progress` ([kanban-markdown](SKILL.md) § Feature Areas)

**Output:** drift bullets under **## Audit findings** on the audit card; link spawned fix cards. **Do not** silently fix drift during the audit turn.

## Agent workflow

| Situation | Action |
| --------- | ------ |
| User assigns a **feature/bug** card | Resolve card → **pre-implementation card review** — no code yet |
| User assigns an **inquiry** card | Resolve card → research → write **`## Response`** (+ **Label Paths** + **Label Methods** if Feature Areas set) → `review` |
| User asks what to work on | Read **To Do** only; summarize title, path, type, **Feature Areas** |
| User assigns **AGENTS.md governance audit** card | Read-only compare per § Periodic AGENTS.md governance audit → **## Audit findings** → `review` (no fixes unless asked) |
| Feature/bug card review complete | Resolve **Feature Areas** → **Label Paths** + **Label Methods** → **Decisions** (feature) or **Corrective Action** (bug) → `todo` → `in-progress` → implement |
| Inquiry card complete | **`## Response`** on card → `review` (no code by default) |
| User spawns inquiry recommendations | § Spawn from inquiry → create **todo** feature/bug cards with `epic`, AC, Label Paths, Label Methods, Decisions |
| `check_governance_parity.py` finds drift | Script runs `check_area_schema_parity` for areas with `agents_skill` (skill/rule files, `lesson_routing_row`, `lesson_signatures`); registry path compare skips schema-internal lesson paths; auto-spawns **todo** cards (epic `GovernanceDriftAlert`; priority from severity) with **## Alert**, **## Feature Areas**, **## Label Paths**, **## Corrective Action** — agent refines on pickup; `--no-spawn-cards` to disable |
| Finishing implementation | Staged pytests green → **update feature-areas.yaml** → **review/update docs/** ([docs-maintenance](../docs-maintenance/SKILL.md)) → **check off AC `[x]`** → `in-progress` → `review` |
| User assigns QA Review on a Review card | Read **`## QA Review`** → implement → check off QA bullets (+ AC if satisfied) → staged pytests green → **update feature-areas.yaml** → **review/update docs/**; stay in **Review** |
| User verified in app | **User** moves `review` → `done` only when **`## QA Review`** are done (or waived) — agents do not |
| New feature request | Create in **`todo`** with **`## Feature Areas`**; never Backlog unless asked |
| New inquiry | Create in **`todo`** with **`## Description`**, `labels: ["inquiry"]`; Feature Areas optional |
| New agent / governance task | Create in **`todo`** with **`## Description`**, **`## Feature Area`** (default `Agent Workflow`), `labels: ["agent"]` |
| Backlog / prioritization | **Do not** — user manages Backlog |
| Ambiguous card reference | List matching To Do cards; ask user to pick |

## Feature area registry (mandatory maintenance)

**Hard constraint:** after **every implementation** (initial feature work **or** QA Review fixes), the agent **MUST**:

1. Update [docs/feature-areas.yaml](../../docs/feature-areas.yaml)
2. Review and update affected files under **`docs/`** per [docs-maintenance](../docs-maintenance/SKILL.md)

…before moving to **Review** or ending the turn. **No exceptions.**

Implementation often creates new files, splits modules, or adds tests — the registry must stay current.

**When to update:**

| Change | Registry action |
| ------ | ----------------- |
| New file created | Add path under the touched feature area(s) (`paths`, `wiring`, or `tests`) |
| New user-facing surface (panel, tab, pipeline) | Add a new area entry with `summary`, paths, `related` |
| File renamed or removed | Update or remove stale paths |
| New test file | Add under `tests` for the relevant area |
| New handler stable across cards | Add under feature area `handlers` in `docs/feature-areas.yaml` |
| New scoped **agent/kanban rule** (`.cursor/rules/agent-*.mdc`, `kanban-*.mdc`) | Add path under **Agent Workflow** `paths` in `docs/feature-areas.yaml`; keep [AGENTS.md](../../AGENTS.md) area → skills & rules table in sync |

**How to update:**

1. Identify which **`## Feature Areas`** on the card were touched (or infer from changed paths)
2. Edit `docs/feature-areas.yaml` — keep labels stable; match naming in `docs/ui.md` where possible
3. If a label is new, add a full entry; link `related` areas for agent discovery
4. Do **not** defer registry updates to the user or a follow-up turn

**Verify script (optional):**

```bash
python scripts/resolve_feature_areas.py "Render Preview"
```

**Do not** mark implementation complete in self-evaluation until `docs/feature-areas.yaml` and **`docs/`** (per docs-maintenance) reflect the change set **and** satisfied **`## Acceptance Criteria`** on the card are marked `[x]`.

## Related skills

| Skill | When |
| ----- | ---- |
| [agent-triage](../agent-triage/SKILL.md) | Start every task; classify before board edits |
| [repo-map](../repo-map/SKILL.md) | Fallback when **Feature Areas** / **Label Paths** are missing or unclear |
| [targeted-testing](../targeted-testing/SKILL.md) | Staged pytest scope for **Label Paths**; map **Label Methods** test symbols when listed |
| [docs-maintenance](../docs-maintenance/SKILL.md) | Mandatory `docs/` review/update — no exceptions |
| [pre-commit-workflow](../pre-commit-workflow/SKILL.md) | `scripts/pre-commit-pytest.sh` hook order and fixes |
