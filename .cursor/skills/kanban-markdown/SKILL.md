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
**Inquiry:** **`Inquire @card`** (Ask) → chat; **`update`** writes **Response** — [reference.md § Inquiry cards](reference.md#inquiry-cards).
**Plan:** **`Plan @card`** (Plan Mode) → chat; **`plan approved`** / **`update`** writes **Recommendation** —
[reference.md § Plan cards](reference.md#plan-cards).
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

Epic **`KanbanCardScope`** (ks0–ks2 **done**): active templates use **Product**, **Tests**, and
**Docs**; **Acceptance Criteria** are behavior-only. Templates: [reference.md § Kanban card scope](reference.md#kanban-card-scope-product--tests--docs). Epic **`KanbanCardScope`** archived 2026-06-28 — do not reuse `epic:` (see `docs/epics-closed.yaml`). Parsers dual-read legacy **Label** on `done/` / `archived/` cards only (Signature: `kanban-card-scope-schema`). **Tests → Verify (agent)** cites `scripts/pre-commit-pytest.sh`; draft **Tests → Files** via `resolve_card_tests.py` (Signature: `precommit-pytest-scope-mismatch`).

| Section | Who | Content |
| ------- | --- | ------- |
| **`## Feature Areas`** | User | Product labels (`Render Preview`, …) |
| **`## Feature Area`** | User (agent cards) | One label; default `` `Agent Workflow` `` |
| **`## Product Paths`** | Agent | Product code paths from [docs/feature-areas.yaml](../../docs/feature-areas.yaml) — no `tests/` |
| **`## Product Methods`** | Agent | Symbols to edit — `path` — `symbol`, … |
| **`## Tests`** | Agent | **Files**, **Methods**, **Verify (agent)** — pytest scope; `scripts/pre-commit-pytest.sh` authoritative |
| **`## Docs`** | Agent | Doc paths + § hints; seed from area `docs:` in yaml |
| **`## Label Paths`** / **`## Label Methods`** | _(legacy)_ | **`done/` / `archived/`** cards only — parsers read as Product |

**Registry:** [docs/feature-areas.yaml](../../docs/feature-areas.yaml). Resolve before coding. After
seeding `agents_skill` / `agents_rules`, run `python3 scripts/sync_agents_area_table.py --write` —
Signature: `governance-area-schema-agents-table-sync`.

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

Rule: [kanban-inquiry-cards.mdc](../../rules/kanban-inquiry-cards.mdc). **`Inquire @card`** + Ask Mode;
**Response** on card after **`update`** — [reference.md § Inquiry cards](reference.md#inquiry-cards).

### Plan cards

Rule: [kanban-plan-cards.mdc](../../rules/kanban-plan-cards.mdc). **`Plan @card`** + Plan Mode;
**Recommendation** on card after approval — [reference.md § Plan cards](reference.md#plan-cards).
Signature: `kanban-cursor-mode-gates`.

### Commit-issue cards

Rule: [kanban-commit-issue-cards.mdc](../../rules/kanban-commit-issue-cards.mdc). Auto-created on failed
commit. Review → user approves → implement.

## Spawn from inquiry

When spawning from a forward-feedback **`ff-*`** item, add **`Forward feedback:`** `` `ff-*` `` to
child **Context** and run `resolve_forward_feedback.py --link` after creating the card — Signature:
`forward-feedback-resolution-tracking`.

When the user asks to **implement recommendations**, **spawn follow-ups**, or **create cards from inquiry**:

1. Read **`## Response`** → **Suggested follow-up cards**
2. Create `.devtool/features/{id}.md` per item — `status: "todo"`, **never Backlog**
3. Set `labels` by work type: `feature` / `bug` / **`agent`** (governance) / `inquiry` (research)
4. Set `epic: "{PascalCase}"`, `order` after existing todo cards
5. Fill review-ready sections: **AC** (behavior), **Product** + **Tests** + **Docs**, **Decisions** (or **Corrective Action** for bugs)
6. Parent inquiry: **`## Spawned feature cards`** table; bump `modified`
7. **Do not** move spawned cards to `in-progress` until user assigns

Phased epics: shared `epic`; implement in `order` unless user re-prioritizes. Examples:
`DesignFailureMemorySystem`, `GovernanceDriftAlerts`, `GovernanceCompact` (gc0–gc7),
`LessonsCoverageMetric`, `ForwardFeedbackRegistry` (ff0–ff3, closed 2026-06-27), `DocsGovernanceSplit`
(dg0–dg3, closed 2026-06-27 — layout schema: [reference.md](reference.md) § Docs governance layout;
Signature: `docs-governance-split`).

Full spawn body table and Response examples: [reference.md § Spawn from inquiry](reference.md#spawn-from-inquiry).

## Card label gate

Read frontmatter `labels` **before** any work. Invalid → **stop** ([kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc)).

**New kanban label (agent governance cards):** add scoped `kanban-*-cards.mdc`, append to
`KANBAN_CARD_TYPE_RULE_NAMES`, card-gates §3, agent-routing § Kanban card type,
`docs/feature-areas.yaml` `agents_rules`/`paths`, AGENTS area table, and kanban_rule_glob test stub
same turn — Signature: `governance-compact-kanban-rule-globs`.

| `labels` | Action |
| -------- | ------ |
| `feature`, `bug`, `agent`, `inquiry`, `plan`, `commit-issue` | Matching scoped rule — [agent-routing.mdc](../../rules/agent-routing.mdc) § Kanban card type |
| missing, `[]`, unknown | **Stop** — user must fix |

## Reading the board

**Default:** To Do only.

1. Grep `status: "todo"` under `.devtool/features/`
2. Sort by `order` (lexicographic fractional index)
3. Read `labels`, Feature Areas / Feature Area, **Product** + **Tests** + **Docs**
4. **Label gate** — invalid → stop
5. **Feature / bug / agent / commit-issue:** pre-implementation card review — no code yet
6. **Inquiry / plan:** **`Inquire @card`** / **`Plan @card`** in chat — **Response** / **Recommendation** only after `update` or approval
7. After review → `todo` → `in-progress`

**Governance epics** (`ArtifactsDocYaml`, `LessonsCoverageMetric`, `GovernanceAreaSchema`): read To Do +
Backlog when user assigns epic; sort by `order` (`a0`–`a9`).

For in-progress/review cards: grep by status when user names the card. Review cards: read **`## QA Review`**.

## Pre-implementation card review (required)

**Feature, bug, agent cards.** Inquiry: § Inquiry cards (rule). **Commit-issue:** prior lessons during
**review** before Root Cause / Corrective Action.

**No code** until this step completes:

1. Read full card; confirm user sections present
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
(4) full done card only when still ambiguous.

**Forward-feedback backlog (not prior-lessons citations):** when the user asks for top-N gc5
questions by category (e.g. "top 3 codebase questions"), read `docs/forward-feedback-index.yaml` and
run `resolve_forward_feedback.py --category … --top N` after the lessons index — Signature:
`forward-feedback-index` ([docs/governance/forward-feedback.md](../../docs/governance/forward-feedback.md);
Signature: `docs-governance-split`).
For open-depth metrics use `--report` (optional `--stale-days N`); parity advisory:
`check_governance_parity.py --forward-feedback-stale` — Signature: `forward-feedback-stale-metrics`.
Do not grep done cards for ranking; Card Done runs `build_forward_feedback_index.py` after
`build_lessons_index.py` when lessons ran — Signature: `forward-feedback-card-done-ingest`.

```bash
python3 scripts/resolve_prior_lessons.py --epic "RenderEngine" "Render Preview" \
  --paths helpers/orbit_face_textures.py
```

Record on card: `**Prior lessons (YYYY-MM-DD):**` under Decisions or Corrective Action. **C4 pass
(per-card):** ≥1 accepted cite on eligible active cards — not every surfaced lesson; aggregate C4
remains advisory (Signature: `lessons-coverage-c4-per-card-threshold`). **Block format:** no line
starting with `**` inside the block after the header — use `- ` group bullets; cite done stems
including commit-issue `T` timestamps and drift hash ids — Signature:
`lessons-coverage-c2-c3-audit` ([reference.md § Card Done](reference.md#card-done--lessons-learned-capture)).
Block boundary: next `##` heading only — mid-block `**QA follow-up**` does not truncate.

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
3. **Refresh** Feature Areas / Product / Tests / Docs when scope changed
4. Bump `modified`

Rule: [kanban-review-qa.mdc](../../rules/kanban-review-qa.mdc). Examples: [reference.md § User-reported QA fixes](reference.md#user-reported-qa-fixes).

## Card Done — lessons learned capture

On user **QA-complete / Done** signal (see [reference.md § QA-complete → Card Done](reference.md#qa-complete--card-done-trigger-table); Signature: `card-done-agent-move-qa-complete`), the **agent** moves the card to `done/` and runs this section **same turn**:

| `labels` | Action |
| -------- | ------ |
| `feature`, `bug`, `agent`, `commit-issue` | **Move** to `done/` + lessons + forward feedback (below) |
| `inquiry` | **Move** to `done/` only — **no** lessons or forward feedback |

**Agent must run in that turn:**

1. Read card — Decisions / Corrective Action, QA follow-ups, Context
2. Distill durable lessons (symptom → fix pattern → tests)
3. Update **≥1 skill** + **≥1 rule** + relevant **docs** / registry. **Schema epics** (ks0/cm0
   pattern): ship full template/matrix in **reference.md** first; SKILL summary + pointer; scoped
   rules in the next phase — Signature: `kanban-cursor-mode-gates`.
4. Add **`## Lessons captured (YYYY-MM-DD)`** on card (edit `done/{id}.md` if moved)
5. Add **`## Forward-looking feedback (YYYY-MM-DD)`** on the card **after** Lessons captured —
   card-specific items (not boilerplate). Six categories (≥1 item each): governance, skill,
   rule, codebase, prompt pattern, routing. Each item: **Question**, **Risk Level** (1–5),
   **Priority**, **Impact Scope** (local / multi-card / system-wide), **References**,
   **Mitigation** on every max-tier item, **Detail** when risk ≥ 3; **Importance**
   (Primary/Secondary/Tertiary) when ≥2 items share max risk — ranking in
   [reference.md § Forward-looking feedback](reference.md#forward-looking-feedback).
   Optional **`ff-*`** back-reference in **References** when the question maps to an indexed
   item (Signature: `forward-feedback-card-done-ingest`). Signature: `card-done-forward-feedback`.
6. When lessons ran, run `python3 scripts/build_lessons_index.py`; curate `lesson_signatures`
   when applicable (e.g. `kanban-card-scope-schema` after KanbanCardScope ks2 Done — Signature:
   `feature-areas-lesson-pointers`) — then `python3 scripts/build_forward_feedback_index.py` (Signature:
   `forward-feedback-card-done-ingest`). Surface stderr dedup warnings in chat as
   **`### Forward feedback dedup`** (non-blocking, before **`### Top forward feedback`**).
7. After writing the card block, surface top 3 items in chat (`### Top forward feedback` before
   handoff — agent-self-evaluation §7).
8. Card Done turns only — not per-turn §6 chat feedback.

Optional `artifacts:` tail — [docs/governance/lessons-and-coverage.md](../../docs/governance/lessons-and-coverage.md) § Lessons captured `artifacts:` (Signature: `docs-governance-split`).
Recommended for C2 promotion-quality scoring (`check_lessons_coverage.py`); not required for Done.
Use `doc:lessons-index.yaml` (explicit extension). Signature: `artifacts-doc-yaml-normalize`.
Inline `` `sig:slug` `` on lesson bullets is also indexed — Signature: `lessons-index-inline-sig-backtick`;
re-run `build_lessons_index.py` after Done when seeded `lesson_signatures` drifted.

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

**Agent** (`review` → `done`) — on user **QA-complete / Done** signal ([reference § QA-complete triggers](reference.md#qa-complete--card-done-trigger-table)):

- Update frontmatter (`status: done`, `completedAt`, `modified`)
- Move `.devtool/features/{id}.md` → `done/{id}.md` (remove active copy)
- Run § Card Done on `done/{id}.md` **same turn** (`feature`/`bug`/`agent`/`commit-issue` only)
- **Not** `archived/` — batch archive is a separate gate (reference § Archive group)

**Agent** (`done/` → `archived/`) — on user **archive group {Name} complete** only (or **epic done
archive** on a single-epic product group — gel0 + gel3 same turn; set `archiveGroup:` on all members):

- Verify manifest via `resolve_archive_group.py --group {Name} --status`
- Move listed members `done/{id}.md` → `archived/{id}.md`; keep `status: "done"`; bump `modified`
- Refresh active card Context/Decisions links (`done/` → `archived/`); Signature:
  `kanban-card-stale-dependency-links`
- Write **`## Archive batch (YYYY-MM-DD)`** on anchor — reference § Archive group (template in reference)

**Inquiry** `review` → `done`: agent or user may move file — **no** Card Done body sections.

File format, fractional `order`, creating cards: [reference.md § File format](reference.md#file-format).

## Periodic AGENTS.md governance audit

**Primary governance cadence:** epic-completion audit when user confirms an epic is complete —
[reference.md § Epic audit](reference.md#epic-audit-gel0--agent-turn). Use
`python3 scripts/resolve_epic_cards.py --epic {Name} --status` before parity runs. Emit
**`### Epic summary`** (gel4) on the audit turn — not on Card Done; Signature:
`governance-epic-completion-summary`.

**Optional backstop** (quarterly or ~90 days without epic close): user runs
`python3 scripts/create_governance_audit_card.py`; agent compares artifacts read-only → **## Audit findings**.

Full checklist: [reference.md § Periodic AGENTS.md governance audit](reference.md#periodic-agentsmd-governance-audit).
Signature: `governance-epic-completion-audit`.

## Agent workflow

| Situation | Action |
| --------- | ------ |
| Feature/bug card assigned | Pre-implementation review → implement |
| Inquiry assigned | Research → **Response** → `review` |
| What to work on? | To Do only; summarize title, path, type |
| Governance audit card | Read-only audit → findings → `review` |
| Epic complete (user confirms) | § Epic audit on anchor — parity, lessons, closed registry; **`### Epic summary`** in chat |
| Archive group complete (user confirms) | § Archive group on anchor — batch archive; **`### Initiative summary`** in chat; Signature `governance-archive-group-batch` |
| Spawn from inquiry | § Spawn from inquiry |
| `check_governance_parity.py` drift | Script may spawn todo cards (epic `GovernanceDriftAlert`) |
| Finishing implementation | Pytests → registry → docs → AC `[x]` → `review` |
| QA on Review card | Fix + record + stay in **Review** |
| User **QA-complete / Done** (card named) | Move to **done/** + Card Done same turn — reference § QA-complete triggers |
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
