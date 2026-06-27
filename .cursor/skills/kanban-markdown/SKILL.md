---
name: kanban-markdown
description: >-
  Kanban board lifecycle for agents — To Do queue, gates, spawn, Card Done.
  Card-type detail, templates, and examples: reference.md (load on demand).
  Scoped rules (kanban-*.mdc) are authoritative per label.
---

# Kanban Markdown

**Canonical task queue for agents.** Use this skill — not [docs/roadmap.md](../../docs/roadmap.md).

**On demand:** [reference.md](reference.md) — card templates, section-order examples, file format,
periodic audit checklist, long markdown blocks.

## Agent scope (important)

| Column | Agent |
| ------ | ----- |
| **To Do** (`todo`) | **Read** — work queue |
| **In Progress** (`in-progress`) | **Update** — after card review + **Decisions** / **Corrective Action** |
| **Review** (`review`) | **Update** — implementation complete; QA fixes (§ User-reported QA fixes) |
| **Done** (`done`) | **Do not move** — user only; agent runs **Card Done** for `feature`/`bug`/`agent`/`commit-issue` |
| **Backlog** (`backlog`) | **Ignore** unless user explicitly asks |

Do **not** grep or summarize Backlog when the user asks what to work on.

## How users reference cards

| User says | Agent resolves |
| --------- | -------------- |
| File path under `.devtool/features/` | Read that file |
| Card `id` slug | Grep `id: "…"` under `.devtool/features/` |
| Title | Grep To Do cards; match `#` heading |
| **First / next To Do** | `status: "todo"`, sort by `order`, take first |
| **Continue / finish** + title | Grep `in-progress` or `review` |

Recommended prompts: `Review …`, `Review and update …`, `implement …`, `Kanban: answer inquiry on …`.

**Not a card assignment:** `docs/roadmap.md`, Backlog (unless explicit), epic name only, vague feature with no card.

### Ask-only vs Agent prompts

Classify **before** any edit. Full verb table: [kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2.
Signature: `kanban-prompt-ask-vs-agent`. **Do not** duplicate the Classify table here — canonical
[reference.md](../agent-triage/reference.md) § Classify; AGENTS summary + triage §1 pointer only
(Signature: `governance-compact-classify-ssot`).

| Mode | Trigger (summary) |
| ---- | ----------------- |
| **Ask-only** | `review …` only; bare `@path`; no card; no agent verb |
| **Agent** | `implement`, `update`, `spawn`, `review and update`, `Kanban: answer inquiry on …` |

**Ask-only review** — read card + codebase; report in chat; no edits until user upgrades the verb.

### Feature lifecycle (summary)

```text
User assigns card → pre-implementation card review (no code)
  → resolve Feature Areas → Label Paths + Label Methods
  → prior lessons gate → Decisions (feature/agent) or Corrective Action (bug/commit-issue)
  → todo → in-progress → implement
  → staged pytests green → feature-areas.yaml + docs/ updated
  → AC [x] → review → user Verify / QA → user: done → Card Done lessons (not inquiry)
```

**Bug:** [kanban-bug-cards.mdc](../../rules/kanban-bug-cards.mdc) — **Corrective Action**, not Decisions.
**Inquiry:** research → **Response** only; no code unless user asks.
**Agent:** [kanban-agent-cards.mdc](../../rules/kanban-agent-cards.mdc) — **Description** + **Feature Area**.
**Commit-issue:** [kanban-commit-issue-cards.mdc](../../rules/kanban-commit-issue-cards.mdc) — review before implement.

After **label gate**, load **one** scoped card-type rule for the card's `labels` — mapping in
[agent-routing.mdc](../../rules/agent-routing.mdc) § Kanban card type; do not open every
`kanban-*.mdc`. [kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) stays always-on.
Signature: `governance-compact-kanban-rule-globs`.

## Board location

| Path | Role |
| ---- | ---- |
| `.devtool/features/*.md` | Active cards |
| `.devtool/features/done/*.md` | Completed |
| `.devtool/features/archived/*.md` | Archived — prior lessons gate scans with `done/` |

VS Code `kanban-markdown.featuresDirectory` (default `.devtool/features`).

## Columns

| status | Column |
| ------ | ------ |
| `backlog` | Backlog |
| `todo` | To Do |
| `in-progress` | In Progress |
| `review` | Review |
| `done` | Done (`done/` subfolder) |

**priority:** `critical` | `high` | `medium` | `low`

## Feature Areas vs Label Paths + Label Methods

| Section | Who | Content |
| ------- | --- | ------- |
| **`## Feature Areas`** | User | Product labels (`Render Preview`, …) |
| **`## Feature Area`** | User (agent cards) | One label; default `` `Agent Workflow` `` |
| **`## Label Paths`** | Agent | Resolved paths from [docs/feature-areas.yaml](../../docs/feature-areas.yaml) |
| **`## Label Methods`** | Agent | Symbols to edit — `path` — `symbol`, … |

**Registry:** [docs/feature-areas.yaml](../../docs/feature-areas.yaml). Resolve before coding. After
seeding `agents_skill` / `agents_rules`, run `python3 scripts/sync_agents_area_table.py --write` —
Signature: `governance-area-schema-agents-table-sync`.

```bash
python scripts/resolve_feature_areas.py "Render Preview"
python scripts/resolve_feature_areas.py --handlers "Open Structures Workflow"
python scripts/resolve_feature_areas.py --lessons "Render Preview"
python scripts/resolve_feature_areas.py --list
```

**Label Methods rules:** symbols this card will change only; ≤8 per file, ≤20 total; implementation opens
**Label Methods** first. **Unknown label:** ask user — do not guess. **No Feature Areas:** grep-first.

Examples: [reference.md](reference.md) § Label Paths and Label Methods.

## Card types (rules + reference)

Scoped **`.mdc` rules** are authoritative per label. This skill covers **lifecycle and gates** only.
Templates and long examples: [reference.md](reference.md).

| `labels` | Rule | Reference templates |
| -------- | ---- | ------------------- |
| `["feature"]` | [kanban-feature-cards.mdc](../../rules/kanban-feature-cards.mdc) | [reference.md § Feature cards](reference.md#feature-cards) |
| `["bug"]` | [kanban-bug-cards.mdc](../../rules/kanban-bug-cards.mdc) | [reference.md § Bug cards](reference.md#bug-cards) |
| `["agent"]` | [kanban-agent-cards.mdc](../../rules/kanban-agent-cards.mdc) | [reference.md § Agent cards](reference.md#agent-cards) |
| `["inquiry"]` | [kanban-inquiry-cards.mdc](../../rules/kanban-inquiry-cards.mdc) | [reference.md § Inquiry cards](reference.md#inquiry-cards) |
| `["commit-issue"]` | [kanban-commit-issue-cards.mdc](../../rules/kanban-commit-issue-cards.mdc) | [reference.md § Commit-issue cards](reference.md#commit-issue-cards) |

### Feature cards

Rule: [kanban-feature-cards.mdc](../../rules/kanban-feature-cards.mdc). Section order, AC, Decisions
examples: [reference.md § Feature cards](reference.md#feature-cards).

### Bug cards

Rule: [kanban-bug-cards.mdc](../../rules/kanban-bug-cards.mdc). Use **Corrective Action** — not Decisions.
Templates: [reference.md § Bug cards](reference.md#bug-cards).

### Agent cards

Rule: [kanban-agent-cards.mdc](../../rules/kanban-agent-cards.mdc). Phased epic spawn: § Spawn from inquiry
and [reference.md § Agent cards](reference.md#agent-cards).

### Inquiry cards

Rule: [kanban-inquiry-cards.mdc](../../rules/kanban-inquiry-cards.mdc). **Response** only by default.
Templates: [reference.md § Inquiry cards](reference.md#inquiry-cards).

### Commit-issue cards

Rule: [kanban-commit-issue-cards.mdc](../../rules/kanban-commit-issue-cards.mdc). Auto-created on failed
commit. Review → user approves → implement.

## Spawn from inquiry

When the user asks to **implement recommendations**, **spawn follow-ups**, or **create cards from inquiry**:

1. Read **`## Response`** → **Suggested follow-up cards**
2. Create `.devtool/features/{id}.md` per item — `status: "todo"`, **never Backlog**
3. Set `labels` by work type: `feature` / `bug` / **`agent`** (governance) / `inquiry` (research)
4. Set `epic: "{PascalCase}"`, `order` after existing todo cards
5. Fill review-ready sections: **AC**, **Label Paths**, **Label Methods**, **Decisions** (or **Corrective Action** for bugs)
6. Parent inquiry: **`## Spawned feature cards`** table; bump `modified`
7. **Do not** move spawned cards to `in-progress` until user assigns

Phased epics: shared `epic`; implement in `order` unless user re-prioritizes. Examples:
`DesignFailureMemorySystem`, `GovernanceDriftAlerts`, `GovernanceCompact` (gc0–gc7), `LessonsCoverageMetric`.

Full spawn body table and Response examples: [reference.md § Spawn from inquiry](reference.md#spawn-from-inquiry).

## Card label gate

Read frontmatter `labels` **before** any work. Invalid → **stop** ([kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc)).

| `labels` | Action |
| -------- | ------ |
| `feature`, `bug`, `agent`, `inquiry`, `commit-issue` | Matching rule (table above) |
| missing, `[]`, unknown | **Stop** — user must fix |

## Reading the board

**Default:** To Do only.

1. Grep `status: "todo"` under `.devtool/features/`
2. Sort by `order` (lexicographic fractional index)
3. Read `labels`, Feature Areas / Feature Area, Label Paths, Label Methods
4. **Label gate** — invalid → stop
5. **Feature / bug / agent / commit-issue:** pre-implementation card review — no code yet
6. **Inquiry:** research + **Response** only
7. After review → `todo` → `in-progress`

**Governance epics** (`ArtifactsDocYaml`, `LessonsCoverageMetric`, `GovernanceAreaSchema`): read To Do +
Backlog when user assigns epic; sort by `order` (`a0`–`a9`).

For in-progress/review cards: grep by status when user names the card. Review cards: read **`## QA Review`**.

## Pre-implementation card review (required)

**Feature, bug, agent cards.** Inquiry: § Inquiry cards (rule). **Commit-issue:** prior lessons during
**review** before Root Cause / Corrective Action.

**No code** until this step completes:

1. Read full card; confirm user sections present
2. Resolve Feature Areas → **Label Paths** + **Label Methods**
3. **Prior lessons gate** (§ below) — before Decisions / Corrective Action
4. Check codebase — Label Methods first; one grep per path
5. **Bugs / commit-issue:** Root Cause, AC, Corrective Action
6. **Feature / agent:** Decisions
7. Report clarifications; apply agreed card edits; user approval if needed
8. `todo` → `in-progress`

Rule detail: [kanban-prior-lessons-gate.mdc](../../rules/kanban-prior-lessons-gate.mdc).

## Prior lessons gate (pre-implementation)

**Mandatory** after Label Paths / Label Methods draft, **before** Decisions or Corrective Action.

**Read order:** (1) `docs/lessons-index.yaml` + [agent-triage/reference.md](../agent-triage/reference.md)
§ Lessons by area, (2) `resolve_feature_areas.py --lessons`, (3) `resolve_prior_lessons.py`,
(4) full done card only when still ambiguous.

```bash
python3 scripts/resolve_prior_lessons.py --epic "RenderEngine" "Render Preview" \
  --paths helpers/orbit_face_textures.py
```

Record on card: `**Prior lessons (YYYY-MM-DD):**` under Decisions or Corrective Action. **C4 block
format:** no line starting with `**` inside the block after the header — use `- ` group bullets;
cite done stems including commit-issue `T` timestamps and drift hash ids — Signature:
`lessons-coverage-c2-c3-audit` ([reference.md § Card Done](reference.md#card-done--lessons-learned-capture)).

Optional C4 check before `in-progress`: `python3 scripts/resolve_prior_lessons.py --audit application`
(or full composite via `--audit all`). Exit code 1 when composite &lt; 75% is **threshold failure**, not a
script crash — Signature: `lessons-coverage-c2-c3-audit`.

Full resolver table and skip rules: [reference.md § Prior lessons gate](reference.md#prior-lessons-gate).

## Verify

**Agent (implicit):** staged `scripts/pre-commit-pytest.sh` before **Review** — feature/bug/agent cards.
**Inquiry:** no pytest unless code changed. **`## Verify`** on cards = **user** manual checks only.

## Decisions / Corrective Action / Acceptance Criteria

| Section | Card types |
| ------- | ---------- |
| **Decisions** | feature, agent |
| **Corrective Action** | bug, commit-issue |
| **Acceptance Criteria** | feature, bug — all `[x]` before **Review** |

Do **not** start code with empty or `TBD` Decisions / Corrective Action.

Examples and QA Review workflow: [reference.md](reference.md) § Decisions, § Acceptance Criteria, § QA Review.

## User-reported QA fixes (Review)

When the user reports a Review issue and you fix it:

1. Implement fix (same pytest/docs gates)
2. **Record on card** — `**QA follow-up (YYYY-MM-DD):**` under Decisions (feature/agent) or Corrective Action (bug)
3. **Refresh** Feature Areas / Label Paths / Label Methods when scope changed
4. Bump `modified`

Rule: [kanban-review-qa.mdc](../../rules/kanban-review-qa.mdc). Examples: [reference.md § User-reported QA fixes](reference.md#user-reported-qa-fixes).

## Card Done — lessons learned capture

**User** moves card to `done/`. When user says **Done**:

| `labels` | Action |
| -------- | ------ |
| `feature`, `bug`, `agent`, `commit-issue` | **Run** lessons capture + forward feedback (this section) |
| `inquiry` | **No** lessons or forward feedback — close only |

**Agent must run in that turn:**

1. Read card — Decisions / Corrective Action, QA follow-ups, Context
2. Distill durable lessons (symptom → fix pattern → tests)
3. Update **≥1 skill** + **≥1 rule** + relevant **docs** / registry
4. Add **`## Lessons captured (YYYY-MM-DD)`** on card (edit `done/{id}.md` if moved)
5. Run `python3 scripts/build_lessons_index.py`; curate `lesson_signatures` when applicable
6. Add **`## Forward-looking feedback (YYYY-MM-DD)`** on the card **after** Lessons captured —
   card-specific items (not boilerplate). Six categories (≥1 item each): governance, skill,
   rule, codebase, prompt pattern, routing. Each item: **Question**, **Risk Level** (1–5),
   **Priority**, **Impact Scope** (local / multi-card / system-wide), **References**,
   **Mitigation** on every max-tier item, **Detail** when risk ≥ 3; **Importance**
   (Primary/Secondary/Tertiary) when ≥2 items share max risk — ranking in
   [reference.md § Forward-looking feedback](reference.md#forward-looking-feedback).
   Signature: `card-done-forward-feedback`. After writing the card block, surface top 3 items in
   chat (`### Top forward feedback` before handoff — agent-self-evaluation §7).
7. Card Done turns only — not per-turn §6 chat feedback.

Optional `artifacts:` tail — [docs/development.md](../../docs/development.md) § Lessons captured schema.
Recommended for C2 promotion-quality scoring (`check_lessons_coverage.py`); not required for Done.
Use `doc:lessons-index.yaml` (explicit extension). Signature: `artifacts-doc-yaml-normalize`.
Inline `` `sig:slug` `` on lesson bullets is also indexed — Signature: `lessons-index-inline-sig-backtick`;
re-run `build_lessons_index.py` after Done when seeded `lesson_signatures` drifted.

**Do not** move card to Done for user. **Do not** skip because AC were `[x]` — QA follow-ups matter.

Full artifact table: [reference.md § Card Done](reference.md#card-done--lessons-learned-capture).

## Moving features

**Agent** (`in-progress` → `review`) — feature, bug, agent:

- Staged pytests green
- Update [docs/feature-areas.yaml](../../docs/feature-areas.yaml) — mandatory
- Review/update `docs/` per [docs-maintenance](../docs-maintenance/SKILL.md)
- Mark satisfied AC `[x]`; `status: "review"`; bump `modified`

**Agent** (inquiry → `review`): **Response** complete; no pytest/docs unless code changed.

**User** (`review` → `done`): QA Review done or waived; set `completedAt`; move to `done/`.

File format, fractional `order`, creating cards: [reference.md § File format](reference.md#file-format).

## Periodic AGENTS.md governance audit

Quarterly (suggested) or after large governance epics. User runs
`python3 scripts/create_governance_audit_card.py`; agent compares artifacts read-only → **## Audit findings**.

Full checklist: [reference.md § Periodic AGENTS.md governance audit](reference.md#periodic-agentsmd-governance-audit).

## Agent workflow

| Situation | Action |
| --------- | ------ |
| Feature/bug card assigned | Pre-implementation review → implement |
| Inquiry assigned | Research → **Response** → `review` |
| What to work on? | To Do only; summarize title, path, type |
| Governance audit card | Read-only audit → findings → `review` |
| Spawn from inquiry | § Spawn from inquiry |
| `check_governance_parity.py` drift | Script may spawn todo cards (epic `GovernanceDriftAlert`) |
| Finishing implementation | Pytests → registry → docs → AC `[x]` → `review` |
| QA on Review card | Fix + record + stay in **Review** |
| User verified app | **User** moves to **done** |
| New card request | Create in **todo** with Feature Areas / Description |
| Backlog | **Do not** unless user asks |

## Feature area registry (mandatory maintenance)

After **every implementation** (initial or QA fix):

1. Update [docs/feature-areas.yaml](../../docs/feature-areas.yaml)
2. Review/update `docs/` per [docs-maintenance](../docs-maintenance/SKILL.md)

Before **Review** or handoff. Registry action table: [reference.md § Feature area registry](reference.md#feature-area-registry).

## Related skills

| Skill | When |
| ----- | ---- |
| [agent-triage](../agent-triage/SKILL.md) | Classify every task |
| [repo-map](../repo-map/SKILL.md) | Fallback when Feature Areas missing |
| [targeted-testing](../targeted-testing/SKILL.md) | Staged pytest scope |
| [docs-maintenance](../docs-maintenance/SKILL.md) | Mandatory `docs/` updates |
| [pre-commit-workflow](../pre-commit-workflow/SKILL.md) | Hook order and fixes |
| [reference.md](reference.md) | Card templates, audit checklist, examples |
