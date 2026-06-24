---
name: kanban-markdown
description: >-
  Create, read, update, move, and manage kanban board feature files backed by
  markdown with YAML frontmatter. Use when working with kanban boards, task/feature
  tracking, `.devtool/features/` directories, feature files with status/priority
  frontmatter, or any project management tasks involving markdown-based kanban
  workflows.   Agent fills ## Decisions after pre-implementation card review; user writes ## Feature
  Areas on cards; agent resolves to ## Label Paths via docs/feature-areas.yaml and
  MUST update that registry after every implementation; MUST mark ## Acceptance Criteria [x]
  when moving to review; MUST review and update docs/ per docs-maintenance (no exceptions).
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
| **In Progress** (`in-progress`) | **Update** — move here only **after** pre-implementation card review **and `## Decisions`** are complete |
| **Review** (`review`) | **Update** — move here when implementation is complete (`in-progress` → `review`); implement **`## QA Review`** when the user asks |
| **Done** (`done`) | **Do not move** — user moves here after manual app review **and** any **`## QA Review`** are implemented |
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
Kanban: implement render-selection-2026-06-22 — review the card first.
```

```text
Work on .devtool/features/render-selection-2026-06-22.md
```

```text
  Review and implement the first To Do card.
```

```text
Kanban: implement QA Review on render-selection-2026-06-22.
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

## End-to-end lifecycle

```text
User assigns card (path or title)
  → pre-implementation card review (no code)
  → user resolves clarifications / approves card edits
  → agent resolves ## Feature Areas → ## Label Paths (docs/feature-areas.yaml)
  → agent fills ## Decisions on the card
  → todo → in-progress → implement (Label Paths)
  → staged pytests green
  → agent updates docs/feature-areas.yaml (mandatory)
  → agent reviews and updates docs/ per docs-maintenance (mandatory, no exceptions)
  → agent marks ## Acceptance Criteria [x] for all shipped bullets (mandatory)
  → in-progress → review
  → user runs ## Verify (manual app checks)
  → user adds ## QA Review during review (if any)
  → agent reviews and implements ## QA Review (if any)
  → staged pytests green
  → user: review → done
```

## Board location

| Path | Role |
| ---- | ---- |
| `.devtool/features/*.md` | Active cards (`backlog`, `todo`, `in-progress`, `review`) |
| `.devtool/features/done/*.md` | Completed cards (`done`) |

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

## Feature Areas (user) vs Label Paths (agent)

Users tag cards with **product areas** they understand. Agents resolve those labels to **repo file paths** before coding.

| Section | Who writes | Content |
| ------- | ---------- | ------- |
| **`## Feature Areas`** | **User** (when creating or editing the card) | Stable labels: `Render Tab`, `Render Preview`, `Paint Brush Panel`, … |
| **`## Label Paths`** | **Agent** (during pre-implementation card review) | Resolved paths from [docs/feature-areas.yaml](../../docs/feature-areas.yaml) plus any new files discovered in review |

**Canonical registry:** [docs/feature-areas.yaml](../../docs/feature-areas.yaml) — maps each label → `paths`, `wiring`, `tests`, `related`, `docs`.

Resolve labels before coding:

```bash
python scripts/resolve_feature_areas.py "Render Preview" "Render Selection"
python scripts/resolve_feature_areas.py --list
```

**During pre-implementation card review:** read **`## Feature Areas`** → resolve via registry → write **`## Label Paths`** on the card (dedupe paths; include tests).

**Unknown label:** ask the user or propose a new registry entry; do not guess file paths.

## Label Paths

Repo-relative paths (files or directories) live in a **`## Label Paths`** section in the card body — **not** in frontmatter `labels`.

Recommended card sections (in order):

1. `# Title` + user story / summary
2. `## Acceptance Criteria`
3. `## Out of Scope` (optional)
4. `## Feature Areas` (user — product labels; see § Feature Areas)
5. `## Label Paths` (agent — resolved repo paths after card review)
6. `## Decisions` (agent work only)
7. `## Verify` (optional — user manual checks only; see § Verify)
8. `## QA Review` (optional — user fills during review; see § QA Review)

| Role | Example line |
| ---- | ------------- |
| Primary code | `` `ui/widgets/preview_panel.py` `` |
| Wiring | `` `ui/main_window.py` `` |
| Tests | `` `tests/test_render_preview.py` `` |
| Package | `` `renderers/registry.py` `` |

**Agents picking up a To Do card:**

1. Read **`## Feature Areas`** (user labels) and resolve via [docs/feature-areas.yaml](../../docs/feature-areas.yaml)
2. Write or refresh **`## Label Paths`** on the card before `in-progress` (deduped union of resolved paths + tests)
3. Open listed paths first (files directly; for directories, grep then read targets)
4. Map paths to tests via [targeted-testing](../targeted-testing/SKILL.md) or `scripts/pre-commit-pytest.sh`
5. If **Feature Areas** and **Label Paths** are both missing, fall back to [repo-map](../repo-map/SKILL.md) — do not invent paths
6. Ignore frontmatter `labels` for navigation (legacy badge values like `["ui"]` may remain)

**When creating or updating cards (user):**

- Add **`## Feature Areas`** with 1–5 backtick-quoted labels (e.g. `` `Render Preview` ``)
- Leave **`## Label Paths`** empty or omit — agent fills during card review
- Set frontmatter `labels: []` unless the VS Code board UI needs display badges
- Optional sections: `## Verify` (user manual checks only), `## QA Review` (user fills during review), `## Out of Scope`
- **`## Decisions`** — agent fills after pre-implementation card review (see § Decisions); not optional once review is complete

**When creating or updating cards (agent after review):**

- Add **`## Label Paths`** with resolved repo paths (2–10 bullets); include test paths when known
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
```

## Verify

Cards may include **`## Verify`** for **user** manual checks (app behavior, visual review, etc.). The user may append verify bullets over time.

**Agent responsibility (always — not written on the card):**

- Run staged pytest before moving to **Review**:
  ```bash
  scripts/pre-commit-pytest.sh
  ```
  on files staged for the change (same scope as the pre-commit hook). See [targeted-testing](../targeted-testing/SKILL.md) and [pre-commit-workflow](../pre-commit-workflow/SKILL.md).
- Do **not** add “run staged pytests” (or similar) to **`## Verify`** when creating or editing cards — that is implicit agent work.
- During **pre-implementation card review**, suggest removing pytest lines from **`## Verify`** if present on legacy cards.

**Before `in-progress` → `review`:** staged pytests green **and** any card **`## Verify`** items are for the **user** to run after handoff (manual app review), not blockers unless the card says otherwise.

## Decisions

**Agent responsibility.** Record implementation choices in **`## Decisions`** on the card after **pre-implementation card review** is complete and before moving `todo` → `in-progress`.

**Typical content:** UI placement, data flow, file/API choices, what to reuse vs add, edge-case handling, and anything that locks scope before coding.

**When to write:**

1. Finish **pre-implementation card review** (read card, check codebase, report clarifications/improvements to user)
2. Resolve open clarifications with the user (or get explicit approval to proceed)
3. **Write or update `## Decisions`** on the card — concrete bullets the implementation will follow
4. Bump `modified`, then move `todo` → `in-progress`

**Do not** start application code while **`## Decisions`** is empty, placeholder (e.g. `TBD by AI`), or still disputed.

**Do not** put acceptance criteria, verify steps, or QA items in **`## Decisions`** — those have their own sections.

Example (after card review, before coding):

```markdown
## Decisions

- Group dropdown in `PreviewPanel` toolbar row; hidden when only one group exists.
- Per-Y PNGs under `output/schematics/_preview/{session}/`; filename pattern `Structure_{group}_{y}.png`.
- Thumbnail strip below toolbar; next/previous buttons navigate the same image list.
- Reuse `RenderWorker` + save-first pattern from render-selection card.
```

## Acceptance Criteria

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

1. Read the full card — especially **`## QA Review`**, **`## Feature Areas`**, **`## Label Paths`**, and **`## Out of Scope`**
2. **Pre-QA review** — confirm each item is clear and in scope; ask the user about ambiguities before coding
3. Implement all open **`## QA Review`** bullets (or the subset the user names)
4. Run `scripts/pre-commit-pytest.sh` on staged paths — same gate as before **Review**
5. Mark implemented bullets done (`[x]`) and bump `modified`
6. Leave `status: "review"` — the **user** moves to **Done** after they accept the fixes

**Do not** move a card to **Done** while **`## QA Review`** has unchecked items — unless the user explicitly says to defer or drop them.

**Do not** add pytest or other implicit agent checklist items to **`## QA Review`** — those belong in agent workflow (see § Verify).

**Before `review` → `done`:** user manual **`## Verify`** checks complete **and** all **`## QA Review`** implemented (or explicitly waived by the user). Agents implement QA items; only the **user** performs the final move to **Done**.

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

## Reading the board

**Default for agents:** To Do column only.

1. `Grep` for `status: "todo"` under `.devtool/features/`
2. Sort matches by `order` (lexicographic fractional index)
3. Read each card’s **`## Feature Areas`** and **`## Label Paths`**, then title and other sections (`## Acceptance Criteria`, `## Decisions`, `## Verify`, `## QA Review`)
4. Run **pre-implementation card review** (see below) — do **not** implement yet
5. After review is complete, move `todo` → `in-progress` and implement from **Label Paths**

Only read **Backlog** when the user explicitly asks about backlog cards.

For a card already in progress, grep `status: "in-progress"` or `status: "review"` if the user names that card or asks to continue/finish it. For **Review** cards, also read **`## QA Review`** — the user may assign implementation of those items next.

## Pre-implementation card review (required)

**Before any code changes**, review the To Do card for clarifications and improvements. **Implementation is not allowed** until this step is complete.

1. Read the full card — acceptance criteria, **feature areas**, out of scope, verify
2. **Resolve `## Feature Areas`** via [docs/feature-areas.yaml](../../docs/feature-areas.yaml) → write **`## Label Paths`** on the card
3. **Check against the codebase** — skim resolved paths only as needed to spot gaps or conflicts
4. **Report to the user:**
   - **Clarifications** — ambiguities, missing scope, or acceptance criteria that need a user answer
   - **Improvements** — suggested edits to the card (wording, scope, feature areas)
5. **Resolve before implementing:**
   - Apply agreed card improvements to the `.md` file (bump `modified`)
   - Get explicit user answers for clarifications, or explicit user approval to proceed when none remain
   - **Write `## Decisions`** on the card (see § Decisions) — implementation choices locked before code
6. **Then** move the card `todo` → `in-progress` and start implementation

**Do not** move to **In Progress**, edit application code, or run implementation work while clarifications are open or card improvements are still pending user agreement.

If the user only asked to review the card (no implementation), stay in **To Do** and do not move the card.

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
labels: []
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
- `labels`: keep `[]` for agents; path references belong in **`## Label Paths`** in the body
- Order: `"double-quoted"` fractional index
- Field order: `id`, `status`, `priority`, `assignee`, `dueDate`, `created`, `modified`, `completedAt`, `labels`, `order`

**Existing cards** may include optional `epic: null` between `assignee` and `dueDate`. Preserve that field and its position when editing those files; omit `epic` on new cards unless the user asks for it.

## Fractional index ordering

When **creating** a card in a column:

- Empty column → `"a0"`
- Append after last item → increment trailing char: `"a0"` → `"a1"` … `"a9"` → `"aA"` (base-62: `0-9`, `A-Z`, `a-z`)

Drag-and-drop reordering is handled by the extension; agents only need append logic for new cards.

## Creating features

**Do not create cards in Backlog** unless the user explicitly asks.

When the user requests a new tracked item:

1. Ask which column, or default to **`todo`** if they want the agent to pick it up
2. **ID:** lowercase title → keep `a-z 0-9 - space` → spaces to `-` → collapse/trim hyphens → truncate 50 chars → append `-YYYY-MM-DD` (or `feature-YYYY-MM-DD` if empty)
3. **Timestamps:** `created` and `modified` = now (ISO 8601); `order` = after last in target column
4. **Body:** `# Title`, acceptance criteria, **`## Feature Areas`** (user labels); leave **`## Label Paths`** and **`## Decisions`** for the agent; optional `## Verify` (user manual checks only — no pytest lines); frontmatter `labels: []`
5. **Done on create:** set `completedAt`, write under `done/`

## Updating features

- Always bump `modified`
- Never change `id` or `created`
- Preserve exact serialization format

## Moving features

Update `status` and `modified`. File stays in `.devtool/features/` until moved to **Done**.

**Agent completes implementation** (`in-progress` → `review`):

- Run `scripts/pre-commit-pytest.sh` on staged paths (agent verify — see § Verify)
- **Update [docs/feature-areas.yaml](../../docs/feature-areas.yaml)** — mandatory (see § Feature area registry)
- **Review and update `docs/`** — mandatory per [docs-maintenance](../docs-maintenance/SKILL.md) (no exceptions)
- **Mark all satisfied `## Acceptance Criteria` bullets `[x]`** — mandatory (see § Acceptance Criteria)
- Set `status: "review"`
- Bump `modified`
- Leave `completedAt: null`
- File remains in `.devtool/features/{id}.md`

**User accepts after manual app review** (`review` → `done`) — **user only**, not the agent:

- All **`## QA Review`** bullets checked or explicitly waived
- Set `completedAt` to now
- Move `{id}.md` → `done/{id}.md`

**From `done` back to active** (user only):

- Set `completedAt` to `null`
- Move `done/{id}.md` → `{id}.md`

## Agent workflow

| Situation | Action |
| --------- | ------ |
| User assigns a card (path, id, or title) | Resolve card → **pre-implementation card review** — no code yet |
| User asks what to work on | Read **To Do** only; summarize title, path, **Feature Areas** |
| Card review complete | Resolve **Feature Areas** → **Label Paths** → **Decisions** → `todo` → `in-progress` → implement |
| Finishing implementation | Staged pytests green → **update feature-areas.yaml** → **review/update docs/** ([docs-maintenance](../docs-maintenance/SKILL.md)) → **check off AC `[x]`** → `in-progress` → `review` |
| User assigns QA Review on a Review card | Read **`## QA Review`** → implement → check off QA bullets (+ AC if satisfied) → staged pytests green → **update feature-areas.yaml** → **review/update docs/**; stay in **Review** |
| User verified in app | **User** moves `review` → `done` only when **`## QA Review`** are done (or waived) — agents do not |
| New feature request | Create in **`todo`** with **`## Feature Areas`**; never Backlog unless asked |
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
| Card introduced a new label | Add area entry or map label → existing area |

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
| [targeted-testing](../targeted-testing/SKILL.md) | Staged pytest scope for **Label Paths**; required before **Review** |
| [docs-maintenance](../docs-maintenance/SKILL.md) | Mandatory `docs/` review/update — no exceptions |
| [pre-commit-workflow](../pre-commit-workflow/SKILL.md) | `scripts/pre-commit-pytest.sh` hook order and fixes |
