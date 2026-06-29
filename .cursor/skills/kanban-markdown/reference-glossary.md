# Kanban card sections (glossary)

Split from [reference.md](reference.md) (krt3 — Signature: `governance-thin-kanban-reference`, `kanban-card-section-glossary`). Lifecycle gates: [SKILL.md](SKILL.md).

## Kanban card sections (glossary)

Epic **`KanbanCardCapturePolicy`** (ccp0–ccp3 **closed 2026-06-28**). SSOT for **where agents put content** — one purpose
per section — and when to capture **Lessons learned**, **Forward-looking feedback**, and in-flight
**Epic coordination**. Signature: `kanban-card-section-glossary`. **ccp1:** full glossary below;
ccp2 (Card Done cadence enforcement), ccp3 (C1b verify + epic close).

### Row schema

Each glossary row uses these columns:

| Column | Meaning |
| ------ | ------- |
| **Section** | Exact `##` heading (or frontmatter key) |
| **Purpose** | One-line why the section exists |
| **Owner** | **User** or **Agent** (who writes first draft) |
| **When** | Lifecycle gate — spawn, pre-implementation, review, Card Done, epic audit, … |
| **Do** | Required content shape |
| **Don't** | Common mis-placements (see § Anti-patterns) |
| **Labels** | Which `labels` use this section |
| **Machine-read** | Parser / script that consumes the section (or **none**) |

### Glossary (full)

#### Frontmatter and user story

| Section | Purpose | Owner | When | Do | Don't | Labels | Machine-read |
| ------- | ------- | ----- | ---- | -- | ----- | ------ | ------------ |
| `labels` (frontmatter) | Card-type gate | Agent (spawn) / User (fix invalid) | Create | Inline JSON array e.g. `["feature"]`, `["feedback"]` | Empty `[]`; block-list YAML | all | `kanban-card-gates.mdc`; parity spawn |
| `epic`, `order` (frontmatter) | Phased epic grouping | Agent (spawn) / Agent (maintain) | Multi-card spawn | PascalCase `epic:`; phase `order` | Reuse closed epic names | feature, bug, agent when phased | `resolve_epic_cards.py`, `resolve_prior_lessons.py --epic` |
| **Description** | User intent / story | User | Create | Problem statement, constraints | Product paths; pytest; agent plan | all active | none |
| **Feature Areas** | Product-area routing (plural) | User | Create | Backtick-quoted registry labels | Resolve paths yourself — agent uses yaml | feature, bug, inquiry, plan | `resolve_feature_areas.py`, `resolve_prior_lessons.py` |
| **Feature Area** | Single-area routing (agent cards) | User | Create | One backtick-quoted label | Multiple areas | agent | same as Feature Areas |
| **Verify** | Manual app QA checklist | User | Review (optional) | User-visible steps only | Pytest commands (`Tests → Verify`) | feature, bug (optional) | none |

#### Scope (Product / Tests / Docs / AC)

| Section | Purpose | Owner | When | Do | Don't | Labels | Machine-read |
| ------- | ------- | ----- | ---- | -- | ----- | ------ | ------------ |
| **Acceptance Criteria** | Behavior-only ship criteria | User (draft) / Agent (complete) | Pre-review | `- [ ]` / `- [x]` intent bullets | `test_*`, `pytest`, `tests/` paths | feature, bug, agent | none (human gate) |
| **Product Paths** | Product code touch list | Agent | Pre-implementation | Repo paths; no `tests/` | Test files; doc-only paths | feature, bug, agent, commit-issue | `extract_label_paths()` (ks1 alias **Label Paths**) |
| **Product Methods** | Symbols to edit | Agent | Pre-implementation | `path` — `symbol` bullets | Pytest-only symbols | feature, bug, agent, commit-issue | `extract_label_method_symbols()`, drift spawn |
| **Label Paths** / **Label Methods** | Legacy Product alias | Agent | Pre-ks2 cards | Same semantics as Product | New content on active cards — migrate to Product | legacy open cards | `extract_label_paths()` / `extract_label_method_symbols()` — Signature: `kanban-card-scope-schema` |
| **Tests** | Pytest scope | Agent | Pre-review | **Files**, **Methods**, **Verify (agent)** | User manual QA (→ **Verify**) | feature, bug, agent, commit-issue | `resolve_card_tests.py`; **Tests → Files** → `extract_label_paths()` |
| **Docs** | Documentation touch list | Agent | Pre-review | `path` — § hint bullets | Product code paths | feature, bug, agent, commit-issue | none |
| **Out of Scope** | Explicit deferrals | User / Agent | Create / review | Deferred work bullets | Hidden scope — spawn follow-ups instead | optional all | none |

#### Implementation plan

| Section | Purpose | Owner | When | Do | Don't | Labels | Machine-read |
| ------- | ------- | ----- | ---- | -- | ----- | ------ | ------------ |
| **Decisions** | Implementation plan | Agent | Pre-implementation → review | Concrete bullets; `**Prior lessons (YYYY-MM-DD):**` block; `**QA follow-up**` on agent/feature | Root cause prose (→ bug sections); TBD at `in-progress` | feature, agent | `PRIOR_LESSONS_RE` / `resolve_prior_lessons.py`; C4 per-card |
| **Root Cause (current code)** | Why bug/hook failed | Agent | Commit-issue review; bug pre-implementation | Code-linked explanation | On feature/agent cards | bug, commit-issue | none |
| **Corrective Action** | Fix plan | Agent | Pre-implementation → review | Concrete fix steps; `**QA follow-up (YYYY-MM-DD):**` | On feature/agent (→ **Decisions**) | bug, commit-issue | none |
| **Context** | Parent links / epic notes | Agent / User | Spawn / optional | Parent card id; phase table; closed deps | Duplicate **Decisions** | optional all | none |
| **Response** | Inquiry research answer | Agent | After user `update` | Answer + optional spawn table | During `Inquire @card` (chat only) | inquiry | none |
| **Recommendation** | Plan roadmap answer | Agent | After plan approved / `update` | Summary, phased roadmap, spawn list | During `Plan @card` (chat only) | plan | none |

#### Commit-issue capture (auto)

| Section | Purpose | Owner | When | Do | Don't | Labels | Machine-read |
| ------- | ------- | ----- | ---- | -- | ----- | ------ | ------------ |
| **Problem** | Hook failure excerpt | Capture script | Failed `git commit` | Log excerpt from pre-commit | Agent overwrite | commit-issue | `create_commit_issue_card.py` |
| **Ruff rules** | Parsed ruff rule ids | Capture script | Ruff hook failure | Rule codes e.g. `SIM110` | Manual guess from Problem | commit-issue | frontmatter `ruffRules` |
| **Failed Tests** | Pytest paths from hook | Capture script | Pytest hook failure | `tests/…` paths | — | commit-issue | pre-commit-pytest mapping |
| **Staged files** | Paths at failure | Capture script | Failed commit | Staged path list | — | commit-issue | none |

#### Review and QA

| Section | Purpose | Owner | When | Do | Don't | Labels | Machine-read |
| ------- | ------- | ----- | ---- | -- | ----- | ------ | ------------ |
| **QA Review** | User Review findings | User | During review | Open checklist bullets | Agent pytest-only items | feature, bug (optional) | none |
| **`**QA follow-up (YYYY-MM-DD):**`** | Review fix audit trail | Agent | Review fixes | Under **Decisions** (feature/agent) or **Corrective Action** (bug); symptom → fix → test | Chat-only record; skip scope refresh | feature, bug, agent | none |
| **`**Prior lessons (YYYY-MM-DD):**`** | Applied prior-lessons cite | Agent | Pre-implementation | Done/archived stems; `` `sig:…` ``; governance paths — block ends at next `##` only | Mid-block `**` subheadings that truncate parser | feature, bug, agent, commit-issue | `PRIOR_LESSONS_RE`; C4 per-card — Signature: `lessons-coverage-c2-c3-audit` |

#### Epic lifecycle (multi-card)

| Section | Purpose | Owner | When | Do | Don't | Labels | Machine-read |
| ------- | ------- | ----- | ---- | -- | ----- | ------ | ------------ |
| **Epic cards** | Multi-card manifest | Agent (anchor) | Spawn + maintain | `order`, card stem, status columns | Per-phase prose (→ **Handoff**) | agent anchor | `resolve_epic_cards.py --status` |
| **Epic coordination** | In-flight cross-phase instructions | Agent (anchor only) | In-flight epic | Dated append-only bullets | gc5 ff; lessons; status table | agent anchor | none — Signature: `epic-coordination-not-forward-feedback` |
| **Handoff** | One-screen next-phase pointer | Agent (phase member) | Phase close (optional) | Next `order` + stem; link anchor coordination | Full manifest; six-category ff | agent phase | none |
| **Epic audit (YYYY-MM-DD)** | Epic close checklist | Agent (anchor) | gel0 user confirm | Manifest, parity, lessons CLI, Summary | Batch archive same turn when `archiveGroup:` set | agent anchor | `docs/epics-closed.yaml` |
| **Archive batch (YYYY-MM-DD)** | Initiative archive checklist | Agent (anchor) | gel3 user confirm | Group manifest; batch `done/` → `archived/` | On Card Done alone | agent anchor | `resolve_archive_group.py` |
| **Spawned feature cards** / **Spawned follow-up cards** | Child card index | Agent (parent) | After spawn | order, path, label, status | Implementation on parent | inquiry, plan, agent anchor; parent Card Done (feedback spawn) | none |
| **Question** | Open forward-feedback ask | Agent | Spawn **`feedback`** | Single durable question | Six-category parent ff block | feedback | fcp2 `build_forward_feedback_index.py` |
| **Risk assessment** | gc5-style ranking on feedback card | Agent | Spawn / update **`feedback`** | Risk, Impact Scope, References; Detail when risk ≥ 3 | Parent **`## Forward-looking feedback`** on new closes | feedback | fcp2 index ingest — Signature: `forward-feedback-risk-rubric` |
| **Options** | Tradeoffs for user | Agent (optional) | Spawn / update | Bullet choices | Implementation plan (→ **Decisions** on implement) | feedback | none |
| **User decision needed** | Explicit confirm gate | Agent (optional) | Spawn (Risk 5) / update | What user must decide before child spawn | Auto-spawn **feature** on Risk 5 same turn | feedback | none |

#### Card Done capture

| Section | Purpose | Owner | When | Do | Don't | Labels | Machine-read |
| ------- | ------- | ----- | ---- | -- | ----- | ------ | ------------ |
| **Lessons captured (YYYY-MM-DD)** | Promoted artifacts | Agent | Card Done (user QA-complete) | Symptom → fix; optional `artifacts:` tail | Open questions (→ ff); in-flight epic notes | feature, bug, agent, commit-issue | `build_lessons_index.py`; C1–C2 |
| **Forward-looking feedback (YYYY-MM-DD)** | Legacy parent gc5 block (archived) | Agent | Card Done — legacy only; new closes spawn **`feedback`** | Six gc5 categories when present; § Risk assessment rubric fields | Epic transition noise; lessons prose | feature, bug, agent; commit-issue optional | `build_forward_feedback_index.py`; C1b — Signature: `card-done-forward-feedback` |

**Multi-card epic batch close:** anchor **`## Epic coordination`** may defer Card Done (lessons + ff)
on all members until epic complete — cards stay in **review** between phases; consolidated capture
at gel0. Signature: `card-done-forward-feedback-cadence` (ccp2 enforcement).

### Anti-patterns

| Mis-placed content | Wrong section | Correct section | Why |
| ------------------ | ------------- | --------------- | --- |
| "Until ccp2 lands, defer ff" | Forward-looking feedback | **Epic coordination** (anchor) | In-flight transition — not durable future behavior |
| "Until ccp2 lands, defer ff" | Lessons captured | **Epic coordination** (anchor) | Not a promoted artifact yet |
| "Until ccp2 lands, defer ff" | **Decisions** on phase card | **Epic coordination** (anchor) | Cross-phase policy — anchor SSOT |
| "Should we require `--line-counts` on every Card Done?" | Epic coordination | **Forward-looking feedback** | Durable governance question — index when captured |
| Symptom → fix → `artifacts:` | Forward-looking feedback | **Lessons captured** | Lessons = shipped fix; ff = open question |
| Symptom → fix → `artifacts:` | **Decisions** only | **Lessons captured** on Done | Decisions = plan; lessons = promoted outcome |
| Review bug fix narrative | **Decisions** without dated bullet | **`**QA follow-up (YYYY-MM-DD):**`** under Decisions / Corrective Action | Audit trail for Review fixes |
| Review bug fix narrative | **QA Review** only | Implement fix + **QA follow-up** | QA Review = user checklist; agent records fix |
| Pytest command | Acceptance Criteria | **Tests → Verify (agent)** | AC is behavior-only |
| `tests/test_foo.py` path | Product Paths | **Tests → Files** | Product Paths exclude `tests/` |
| Epic phase status prose | Forward-looking feedback | **Epic coordination** or **Handoff** | Transition noise — not ff backlog |
| Six-category ff on every phase close | Card Done (phase member) | Defer to anchor — § Forward-looking feedback cadence | Signature: `card-done-forward-feedback-cadence` |
| Implementation plan | **Corrective Action** | **Decisions** | Corrective Action = bug/commit-issue only |
| Root cause analysis | **Decisions** | **Root Cause** + **Corrective Action** | Bug/commit-issue sections |
| Inquiry answer on card during Inquire | **Response** (premature) | Chat only until `update` | Signature: `kanban-cursor-mode-gates` |
| Hook log dump | **Corrective Action** | **Problem** (preserve) + agent **Root Cause** below | Capture script owns Problem |

Signature: `epic-coordination-not-forward-feedback` (coordination rows above).

### Label matrix

Which sections apply per card type. **●** = required before **review** (or at gate); **○** = optional;
**—** = do not use on that label.

| Section | feature | bug | agent | commit-issue | inquiry | plan | feedback |
| ------- | ------- | --- | ----- | ------------ | ------- | ---- | -------- |
| Description / story | ● | ● | ● | ○ (Problem instead) | ● | ● | ○ (Question) |
| Feature Areas / Feature Area | ● | ● | ● (Feature Area) | ○ | ○ | ○ | ○ |
| Acceptance Criteria | ● | ● | ● | — | — | — | — |
| Product Paths / Methods | ● | ● | ● | ○ | ○ | ○ | ○ |
| Tests | ● | ● | ● | ○ | — | — | ○ |
| Docs | ● | ● | ● | ○ | — | — | ○ |
| Decisions | ● | — | ● | — | — | — | ○ |
| Root Cause | — | ● | — | ● (on review) | — | — | — |
| Corrective Action | — | ● | — | ● (on review) | — | — | — |
| Response | — | — | — | — | ● (after update) | — | — |
| Recommendation | — | — | — | — | — | ● (after approval) | — |
| Problem / Failed Tests / Staged files | — | — | — | ● (capture) | — | — | — |
| Prior lessons block | ● | ● | ● | ● | — | — | — |
| QA Review | ○ | ○ | ○ | — | — | — | — |
| QA follow-up bullets | ● | ● | ● | ○ | — | — | — |
| Epic cards / coordination | — | — | ○ anchor | — | — | — | — |
| Handoff | — | — | ○ phase | — | — | — | — |
| Question / Risk assessment | — | — | — | — | — | — | ● |
| Context (parent path) | — | — | — | — | ○ | ○ | ● |
| Options / User decision needed | — | — | — | — | — | — | ○ |
| Lessons captured | ● Done | ● Done | ● Done | ● Done | — Done | — Done | — Done |
| Forward-looking feedback | ● Done* | ● Done* | ● Done* | ○ Done | — | — | — |
| Epic audit / Archive batch | — | — | ○ anchor | — | — | — | — |

\***New closes:** § [Forward-feedback capture cadence](#forward-feedback-capture-cadence) — lessons
always; spawn **`feedback`** when risk **≥ 3**; **no** mandatory parent ff. Legacy parent gc5:
§ [Forward-looking feedback cadence](#forward-looking-feedback-cadence) (archived / index only).
**inquiry** / **plan** / **feedback** — move only; no lessons or parent-style ff on Done.

**Scoped rules:** pointer-only — [kanban-feature-cards.mdc](../../rules/kanban-feature-cards.mdc),
[kanban-bug-cards.mdc](../../rules/kanban-bug-cards.mdc), [kanban-agent-cards.mdc](../../rules/kanban-agent-cards.mdc),
[kanban-commit-issue-cards.mdc](../../rules/kanban-commit-issue-cards.mdc),
[kanban-inquiry-cards.mdc](../../rules/kanban-inquiry-cards.mdc),
[kanban-plan-cards.mdc](../../rules/kanban-plan-cards.mdc),
[kanban-feedback-cards.mdc](../../rules/kanban-feedback-cards.mdc). Signature: `governance-compact-kanban-split`.

## Feedback cards

**`labels: ["feedback"]`** — risk-gated open questions; spawn from Card Done when risk **≥ 3**.
Schema: **Question**, **Risk assessment**, **Context**; optional **Decisions** before implement.
Rule: [kanban-feedback-cards.mdc](../../rules/kanban-feedback-cards.mdc). Signature: `feedback-label-kanban`.

## Risk assessment rubric

Risk **1–5** on **`feedback`** cards — **≥ 3** spawns index ingest; **5** mandatory same turn.
Fields: Risk, Impact Scope, References; Detail when risk **≥ 3**. Signature: `forward-feedback-risk-rubric`.

**Feedback (fcp1):** capture cadence:
[§ Forward-feedback capture cadence](#forward-feedback-capture-cadence) — Signatures:
`feedback-label-kanban`, `forward-feedback-capture-policy`.
