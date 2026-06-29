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
periodic audit checklist, long markdown blocks. **Glossary SSOT:** [reference-glossary.md](reference-glossary.md)
(Signature: `kanban-card-section-glossary`). **KanbanReferenceThin** closed — see
[epics-closed.yaml](../../docs/epics-closed.yaml); `--duplication-threshold` passes (caps **1000** /
**1200**) — Signature: `governance-thin-kanban-reference`; handbook
[audit-and-compaction.md](../../docs/governance/audit-and-compaction.md) § KanbanReferenceThin.

## Agent scope (important)

| Column | Agent |
| ------ | ----- |
| **To Do** (`todo`) | **Read** — work queue |
| **In Progress** (`in-progress`) | **Update** — after card review + **Decisions** / **Corrective Action** |
| **Review** (`review`) | **Update** — implementation complete; QA fixes (§ User-reported QA fixes) |
| **Done** (`done`) | Agent moves on **QA-complete** signal + Card Done same turn (`feature`/`bug`/`agent`/`commit-issue`); **`inquiry`**: move only — no lessons |
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

Recommended prompts: `Plan @card`, `Inquire @card`, `review …`, `update …`, `plan approved`,
`implement …`, `review and update …` (rare). Legacy: `Kanban: answer inquiry on …` → prefer
**Inquire** then **update** ([reference.md § Cursor mode gates](reference.md#cursor-mode-gates-plan--inquire--verbs)).

**Not a card assignment:** `docs/roadmap.md`, Backlog (unless explicit), epic name only, vague feature with no card.

### Cursor mode vs prompt verbs (summary)

Canonical matrix: [reference.md § Cursor mode gates](reference.md#cursor-mode-gates-plan--inquire--verbs)
(Signature: `kanban-cursor-mode-gates`). Scoped rules: [kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2,
[kanban-plan-cards.mdc](../../rules/kanban-plan-cards.mdc), [kanban-inquiry-cards.mdc](../../rules/kanban-inquiry-cards.mdc).
Do not duplicate the full table here.

| Mode (summary) | Trigger (summary) |
| -------------- | ----------------- |
| **Ask** + chat-only **`review`** | `review …` only; bare `@path`; **`Inquire @card`** |
| **Plan** + chat-only plan | **`Plan @card`** — no card edit until approval |
| **Agent** | `update …`, `plan approved`, `implement`, `spawn`, rare `review and update` / `plan and update` |

**`review …` only** — read card + codebase; report in chat; **never** edits the card file.

### Feature lifecycle (summary)

```text
User assigns card → pre-implementation card review (no code)
  → resolve Feature Areas → Product + Tests + Docs
  → prior lessons gate → Decisions (feature/agent) or Corrective Action (bug/commit-issue)
  → todo → in-progress → implement
  → staged pytests green → feature-areas.yaml + docs/ updated
  → AC [x] → review → user Verify / QA → user: done → Card Done lessons (not inquiry)
```

**Bug:** [kanban-bug-cards.mdc](../../rules/kanban-bug-cards.mdc) — **Corrective Action**, not Decisions.
**Inquiry:** **`Inquire @card`** (Ask) → chat; **`update`** writes **Response**.
**Plan:** **`Plan @card`** (Plan Mode) → chat; **`plan approved`** / **`update`** writes **Recommendation**.
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

## Feature Areas vs Product / Tests / Docs

Active templates: **Product**, **Tests**, **Docs**; behavior-only **AC** — [reference.md § Kanban card scope](reference.md#kanban-card-scope-product--tests--docs). Resolve via [docs/feature-areas.yaml](../../docs/feature-areas.yaml); `sync_agents_area_table.py --write` after yaml `agents_skill` edits.

```bash
python scripts/resolve_feature_areas.py "Render Preview"
python scripts/resolve_feature_areas.py --handlers "Open Structures Workflow"
python scripts/resolve_feature_areas.py --lessons "Render Preview"
python scripts/resolve_feature_areas.py --list
```

**Product Methods rules:** symbols this card will change only; ≤8 per file, ≤20 total; open
**Product Methods** first (grep symbols before broad file reads). **Unknown label:** ask user — do not guess. **No Feature Areas:** grep-first.

**Review gate:** **Product** + **Tests** + **Docs** must be complete (no `_TBD_`) before **in-progress → review** on feature/bug/agent cards.

Examples: [reference.md](reference.md) § Kanban card scope (Product / Tests / Docs).

## Card types (rules + reference)

Scoped **`.mdc` rules** are authoritative per label. This skill covers **lifecycle and gates** only.
Templates and long examples: [reference.md](reference.md).

| `labels` | Rule | Templates |
| -------- | ---- | --------- |
| `["feature"]` | [kanban-feature-cards.mdc](../../rules/kanban-feature-cards.mdc) | [reference.md § Card types](reference.md#card-types-templates) |
| `["bug"]` | [kanban-bug-cards.mdc](../../rules/kanban-bug-cards.mdc) | same |
| `["agent"]` | [kanban-agent-cards.mdc](../../rules/kanban-agent-cards.mdc) | same |
| `["inquiry"]` | [kanban-inquiry-cards.mdc](../../rules/kanban-inquiry-cards.mdc) | same |
| `["plan"]` | [kanban-plan-cards.mdc](../../rules/kanban-plan-cards.mdc) | same |
| `["commit-issue"]` | [kanban-commit-issue-cards.mdc](../../rules/kanban-commit-issue-cards.mdc) | same |
| `["feedback"]` | [kanban-feedback-cards.mdc](../../rules/kanban-feedback-cards.mdc) | same + [reference-glossary.md](reference-glossary.md) |

**Plan:** `Plan @card` + Plan Mode; **commit-issue:** review before implement — Signature:
`commit-issue-review-and-implement-one-shot`. **Feedback:** spawn from Card Done; move-only Done —
Signature: `feedback-label-kanban`.

## Spawn from inquiry

When spawning from a forward-feedback **`ff-*`** item, add **`Forward feedback:`** `` `ff-*` `` to
child **Context** and run `resolve_forward_feedback.py --link` + `--set-status answered` after
closing the spawn card — Signature: `forward-feedback-resolution-tracking`.

When user **discussion closes the question** and requests spawn in the same turn (no implement yet),
run `--link` then `--set-status answered` with resolution citing the spawned card path — do not leave
`open` after spawn.

When the user asks to **implement recommendations**, **spawn follow-ups**, or **create cards from inquiry**:

1. Read **`## Response`** → **Suggested follow-up cards**
2. Create `.devtool/features/{id}.md` per item — `status: "todo"`, **never Backlog**
3. Set `labels` by work type: `feature` / `bug` / **`agent`** (governance) / `inquiry` (research)
4. Set `epic: "{PascalCase}"`, `order` after existing todo cards
5. Fill review-ready sections: **AC** (behavior), **Product** + **Tests** + **Docs**, **Decisions** (or **Corrective Action** for bugs)
6. Parent inquiry: **`## Spawned feature cards`** table; bump `modified`
7. **Do not** move spawned cards to `in-progress` until user assigns

Phased epics: shared `epic`; implement in `order`. Closed epic names: `docs/epics-closed.yaml` only.
Spawn body + gel0/gel3: [reference.md § Spawn, epics, and drift](reference.md#spawn-epics-and-drift).

## Card label gate

Read frontmatter `labels` **before** any work. Invalid → **stop** ([kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc)).

**New kanban label (agent governance cards):** add scoped `kanban-*-cards.mdc`, append to
`KANBAN_CARD_TYPE_RULE_NAMES`, card-gates §3, agent-routing § Kanban card type,
`docs/feature-areas.yaml` `agents_rules`/`paths`, AGENTS area table, and kanban_rule_glob test stub
same turn — Signature: `governance-compact-kanban-rule-globs`.

| `labels` | Action |
| -------- | ------ |
| `feature`, `bug`, `agent`, `inquiry`, `plan`, `commit-issue`, `feedback` | Matching scoped rule — [agent-routing.mdc](../../rules/agent-routing.mdc) § Kanban card type |
| missing, `[]`, unknown | **Stop** — user must fix |

## Reading the board

**Default:** To Do only.

1. Grep `status: "todo"` under `.devtool/features/`
2. Sort by `order` (lexicographic fractional index)
3. Read `labels`, Feature Areas / Feature Area, **Product** + **Tests** + **Docs**
4. **Label gate** — invalid → stop
5. **Feature / bug / agent / commit-issue:** pre-implementation card review — no code yet
6. **Inquiry / plan / feedback:** **`Inquire @card`** / **`Plan @card`** in chat; **feedback** stays
   **`todo`** until user assigns — **Response** / **Recommendation** only after `update` or approval
7. After review → `todo` → `in-progress`

**Governance epics** (`ArtifactsDocYaml`, `LessonsCoverageMetric`, `GovernanceAreaSchema`): read To Do +
Backlog when user assigns epic; sort by `order` (`a0`–`a9`).

For in-progress/review cards: grep by status when user names the card. Review cards: read **`## QA Review`**.

## Pre-implementation card review (required)

**Feature, bug, agent cards.** Inquiry: § Inquiry cards (rule). **Commit-issue:** prior lessons during
**review** before Root Cause / Corrective Action.

**No code** until this step completes:

1. Read full card; confirm user sections present; mis-placed content →
   [reference-glossary.md](reference-glossary.md) (Signature: `kanban-card-section-glossary`)
2. Resolve Feature Areas → **Product Paths** + **Product Methods** + **Tests** + **Docs**
3. **Prior lessons gate** (§ below) — before Decisions / Corrective Action
4. Check codebase — **Product Methods** first; one grep per path; **Tests → Files** for pytest map
5. **Bugs / commit-issue:** Root Cause, AC, Corrective Action
6. **Feature / agent:** Decisions
7. Report clarifications; apply agreed card edits; user approval if needed
8. `todo` → `in-progress`

Rule detail: [kanban-prior-lessons-gate.mdc](../../rules/kanban-prior-lessons-gate.mdc).

## Prior lessons gate (pre-implementation)

**Mandatory** after **Product** + **Tests** + **Docs** draft, **before** Decisions or Corrective Action.

**Read order:** (1) `docs/lessons-index.yaml` + [agent-triage/reference.md](../agent-triage/reference.md)
§ Lessons by area, (2) `resolve_feature_areas.py --lessons`, (3) `resolve_prior_lessons.py`,
(4) full done card only when still ambiguous. **Do not** broad grep on `done/` / `archived/` — Signature:
`governance-index-not-grep` ([reference.md § Index vs folder grep](reference.md#index-vs-folder-grep-acb4)).

**Forward-feedback backlog:** `forward-feedback-index.yaml` + `resolve_forward_feedback.py` — not
prior-lessons citations (Signature: `forward-feedback-index`). Record
`**Prior lessons (YYYY-MM-DD):**` under Decisions / Corrective Action — C4 / block format:
[reference.md § Prior lessons gate](reference.md#prior-lessons-gate); Signature:
`lessons-coverage-c2-c3-audit`.

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
3. **Refresh** Feature Areas / Product / Tests / Docs when scope changed
4. Bump `modified`

Rule: [kanban-review-qa.mdc](../../rules/kanban-review-qa.mdc). Examples: [reference.md § User-reported QA fixes](reference.md#user-reported-qa-fixes).

## Card Done — lessons learned capture

On user **QA-complete / Done** signal (see [reference.md § QA-complete → Card Done](reference.md#qa-complete--card-done-trigger-table); Signature: `card-done-agent-move-qa-complete`), the **agent** moves the card to `done/` and runs this section **same turn**. When the user does **not** name a card, run [reference.md § Disambiguation (card unnamed)](reference.md#disambiguation-card-unnamed) first — Signature: `card-done-disambiguate-multi-review`. **Section placement:** [reference-glossary.md](reference-glossary.md); **ff:** [reference.md § Forward-feedback capture cadence](reference.md#forward-feedback-capture-cadence) — Signatures: `kanban-card-section-glossary`, `card-done-forward-feedback-cadence`, `forward-feedback-capture-policy`.

| `labels` | Action |
| -------- | ------ |
| `feature`, `bug`, `agent`, `commit-issue` | **Move** to `done/` + **lessons** always; **ff** per cadence gate (below) |
| `inquiry`, `feedback` | **Move** to `done/` only — **no** lessons or forward feedback |

**Capture cadence (fcp2):** parent **lessons always**; **no** mandatory parent
`## Forward-looking feedback` on new closes. Spawn **`feedback`** todos when honest risk **≥ 3**;
**Risk 5** → mandatory **`feedback`** spawn same turn (Option A). SSOT:
[reference.md § Forward-feedback capture cadence](reference.md#forward-feedback-capture-cadence);
phase/epic coordination: [reference-glossary.md](reference-glossary.md) — Signatures:
`forward-feedback-capture-policy`, `card-done-feedback-spawn`, `epic-coordination-not-forward-feedback`.

**Agent must run in that turn:**

1. Read card — Decisions / Corrective Action, QA follow-ups, Context; check cadence row above
2. Distill durable lessons (symptom → fix pattern → tests)
3. Update **≥1 skill** + **≥1 rule** + relevant **docs** / registry
4. Add **`## Lessons captured (YYYY-MM-DD)`** on card (edit `done/{id}.md` if moved)
5. Score open questions — spawn **`todo`** **`feedback`** card(s) when risk **≥ 3** (**Risk 5**
   mandatory same turn — Option A). Append **`## Spawned follow-up cards`** on parent with
   feedback paths; after index rebuild add **`Forward feedback:`** `` `ff-*` `` on child **Context**
   and run `resolve_forward_feedback.py --link` when linking spawn — Signature:
   `forward-feedback-resolution-tracking`, `card-done-feedback-spawn`.
6. When lessons ran: `python3 scripts/build_lessons_index.py`; then
   `python3 scripts/build_forward_feedback_index.py` when lessons ran **or** **`feedback`** cards
   were spawned (Signature: `forward-feedback-card-done-ingest`). Dedup → **`### Forward feedback
   dedup`** in chat.
7. **Top-3 chat** (`### Top forward feedback`) — risk **≥ 3** only; include 1–2 only when sole
   items; **omit** when no feedback spawned and no legacy parent ff block written — agent-self-evaluation §7
8. Card Done turns only — not per-turn §6 chat feedback

Optional `artifacts:` tail — [lessons-and-coverage.md](../../docs/governance/lessons-and-coverage.md) § Lessons captured `artifacts:` (Signature: `docs-governance-split`). Recommended for C2 scoring; not required for Done. Use `doc:lessons-index.yaml`; inline `` `sig:slug` `` indexed — re-run `build_lessons_index.py` when `lesson_signatures` drift.

**Do not** skip because AC were `[x]` — QA follow-ups matter. **Do not** run Card Done on agent's own
`review` completion — wait for user QA-complete / Done signal (Review QA fixes stay in **review**).
**Do not** move cards to `archived/` on Card Done — batch archive runs only on user **archive group
{Name} complete** (reference § Archive group; Signature: `governance-archive-group-batch`).

Full artifact table: [reference.md § Card Done](reference.md#card-done--lessons-learned-capture).

## Moving features

**Agent** (`in-progress` → `review`) — feature, bug, agent:

- Staged pytests green
- Update [docs/feature-areas.yaml](../../docs/feature-areas.yaml) — mandatory
- Review/update `docs/` per [docs-maintenance](../docs-maintenance/SKILL.md)
- Mark satisfied AC `[x]`; `status: "review"`; bump `modified`

**Agent** (inquiry → `review`): **Response** complete; no pytest/docs unless code changed.

**Agent** (`review` → `done`) — user **QA-complete / Done**: move to `done/` + § Card Done same turn.
**Archive:** user **archive group {Name} complete** only — [reference.md § Spawn, epics](reference.md#spawn-epics-and-drift).

File format: [reference.md § File format](reference.md#file-format).

## Periodic AGENTS.md governance audit

Epic close (gel0) primary; optional `create_governance_audit_card.py` backstop — [reference.md § Periodic AGENTS.md governance audit](reference.md#periodic-agentsmd-governance-audit).

## Agent workflow

| Situation | Action |
| --------- | ------ |
| Feature/bug/agent assigned | Pre-implementation review → implement → `review` |
| Inquiry / plan | Chat (`Inquire` / `Plan`) → `update` / approval → card section |
| User **Done** (card named) | Move + Card Done — reference § QA-complete triggers |
| Epic / archive close | gel0 / gel3 — reference § Spawn, epics |

## Feature area registry (mandatory maintenance)

After implementation: update [docs/feature-areas.yaml](../../docs/feature-areas.yaml) + `docs/` per [docs-maintenance](../docs-maintenance/SKILL.md).

## Related skills

| Skill | When |
| ----- | ---- |
| [agent-triage](../agent-triage/SKILL.md) | Classify every task |
| [repo-map](../repo-map/SKILL.md) | Fallback when Feature Areas missing |
| [targeted-testing](../targeted-testing/SKILL.md) | Staged pytest scope |
| [docs-maintenance](../docs-maintenance/SKILL.md) | Mandatory `docs/` updates |
| [pre-commit-workflow](../pre-commit-workflow/SKILL.md) | Hook order and fixes |
| [reference.md](reference.md) | Card templates, audit checklist, examples |
