# Agent guide — structure_scripts

**Start here** for Cursor agents. **Agent mode** requires a kanban card, valid `labels`, and an
**agent verb** (`implement`, `update`, `spawn`, …) — see [kanban-card-gates.mdc](.cursor/rules/kanban-card-gates.mdc).
**`review …` only** or no card → **Ask-only** (read-only).

Thin always-on orchestration: [`.cursor/rules/agent-routing.mdc`](.cursor/rules/agent-routing.mdc).  
Full process: [`.cursor/skills/agent-triage/SKILL.md`](.cursor/skills/agent-triage/SKILL.md) → work →
[`.cursor/skills/agent-self-evaluation/SKILL.md`](.cursor/skills/agent-self-evaluation/SKILL.md).

Do **not** use [docs/roadmap.md](docs/roadmap.md) as the task queue.

## Default: kanban-first

| User mode | How work arrives | Agent does |
| --------- | ---------------- | ---------- |
| **Agent mode** | Card named + **agent verb** | [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md); [kanban-card-gates.mdc](.cursor/rules/kanban-card-gates.mdc) §2 |
| **Ask-only** | `review …` only, bare `@path`, no card, or no agent verb | Read-only — suggest `implement` / `review and update` |
| **Governance queue** | User names backlog / audit card | [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Reading the board |

**Ignore Backlog** unless the user names a backlog card. On **QA-complete / Done**, the **agent**
moves cards to `done/` + Card Done same turn (`feature`/`bug`/`agent`/`commit-issue`); **`inquiry`**
/ **`feedback`** → move only — [reference § QA-complete triggers](.cursor/skills/kanban-markdown/reference.md#qa-complete--card-done-trigger-table).

**No implementation without a card** — no surgical/ad-hoc fixes.

### Card label gate

Every card **must** have a recognized `labels` entry (inline JSON array). **Invalid** (missing,
`labels: []`, unknown) → **stop**; user must set `feature`, `bug`, `agent`, `inquiry`, `plan`,
`commit-issue`, or `feedback`.

### Card types (`labels` in frontmatter)

| Label | User provides | Agent provides before `in-progress` |
| ----- | ------------- | ------------------------------------- |
| `feature` | Feature Areas, story, optional AC | **Product** + **Tests** + **Docs**, **Decisions**, AC — [kanban-feature-cards.mdc](.cursor/rules/kanban-feature-cards.mdc) |
| `bug` | Steps, Current/Expected, Feature Areas | Root Cause, AC, **Product** + **Tests** + **Docs**, **Corrective Action** — [kanban-bug-cards.mdc](.cursor/rules/kanban-bug-cards.mdc) |
| `commit-issue` | _(auto)_ Problem + Failed Tests | **Review:** Root Cause + Corrective Action — [kanban-commit-issue-cards.mdc](.cursor/rules/kanban-commit-issue-cards.mdc) |
| `inquiry` | Description; Feature Areas optional | **Response** (after `update`); `Inquire @card` + Ask Mode — [kanban-inquiry-cards.mdc](.cursor/rules/kanban-inquiry-cards.mdc) |
| `plan` | Description; optional Feature Areas | **Recommendation** (after approval); `Plan @card` + Plan Mode — [kanban-plan-cards.mdc](.cursor/rules/kanban-plan-cards.mdc) |
| `agent` | **Description**, **Feature Area** | **Product** + **Tests** + **Docs**, AC, **Decisions** — [kanban-agent-cards.mdc](.cursor/rules/kanban-agent-cards.mdc) |
| `feedback` | _(spawn)_ **Question**, **Risk assessment**, **Context** | Optional scope when user assigns `implement` — [kanban-feedback-cards.mdc](.cursor/rules/kanban-feedback-cards.mdc) |

Resolve **Feature Areas** → **Product** + **Tests** + **Docs** via [docs/feature-areas.yaml](docs/feature-areas.yaml):

```bash
python scripts/resolve_feature_areas.py "Render Preview"
python scripts/resolve_feature_areas.py --handlers "Open Structures Workflow"
python scripts/resolve_feature_areas.py --lessons "Render Preview"
```

## Every turn (non–Ask mode)

```text
1. Classify   → reference § Classify; triage §1 — card + label → one scoped kanban-*-cards.mdc
1b. Failure   → triage §1b grep (signals only)
2. Discover   → reference § Discovery ladder; ≤3 reads then grep/search
3. Work       → Product + Tests + Docs → prior lessons gate → Decisions/CA; Review QA → **QA follow-up**
4. Verify     → ruff E501 on touched `.py`; staged pre-commit-pytest.sh
5. Done       → QA-complete → agent moves `done/` + Card Done (kanban-markdown § Card Done; ff cadence fcp2);
               `build_lessons_index.py` when lessons ran; `build_forward_feedback_index.py` when lessons ran or
               **`feedback`** spawned (Signature: `forward-feedback-card-done-ingest`)
6. Self-eval  → agent-self-evaluation §7; ≥1 skill + ≥1 rule on implementation turns
```

Detail: [agent-triage/SKILL.md](.cursor/skills/agent-triage/SKILL.md), [agent-routing.mdc](.cursor/rules/agent-routing.mdc).

## Maintaining AGENTS.md (routing guide)

**Agents MUST evaluate this file every turn** (self-evaluation §2b check 4). Signature:
`governance-thin-agents-md` — epic history lives in yaml/reference, not here (acb3).

| Change category | SSOT — update same turn |
| --------------- | ----------------------- |
| Signatures, routing steps, card types, area table, handoff | [agent-consistency.mdc](.cursor/rules/agent-consistency.mdc) § **Change → must update** + [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § Consistency matrix |
| Closed epics / gel0 audit / archive groups | [docs/epics-closed.yaml](docs/epics-closed.yaml) + [kanban-markdown/reference.md](.cursor/skills/kanban-markdown/reference.md) § Closed epics registry |

**Scoped rules:** agent/kanban skill edits → [agent-agents-md-maintenance.mdc](.cursor/rules/agent-agents-md-maintenance.mdc).
Governance globs → self-eval §6g. **Periodic audit:** reference § Epic audit —
`create_governance_audit_card.py` (optional). **Drift:** reference § Drift alert examples.

If behavior changed but **AGENTS.md** is stale → handoff **Context load:** `AGENTS.md stale: …` and fix when possible.

## Classify quickly

**Full signal table:** [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § **Classify** —
Signature: `governance-compact-classify-ssot`. Edit reference only; ≤5-row summary:

| Signal | Mode | First read |
| ------ | ---- | ---------- |
| **Review** kanban card only | **Ask-only** | Card + [kanban-card-gates](.cursor/rules/kanban-card-gates.mdc) §2 |
| **`Plan @card`** / **`Inquire @card`** | **Plan** / **Ask-only** | Chat only — **`update`** / **`plan approved`** → Agent |
| **Implement / update / spawn / Done / epic / archive** | **Agent** | Card + [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md); bare Done: [reference § Disambiguation](.cursor/skills/kanban-markdown/reference.md#disambiguation-card-unnamed) |
| Card missing / invalid `labels` | **Block** | [kanban-card-gates](.cursor/rules/kanban-card-gates.mdc) |
| All other signals | *see reference* | [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § Classify + § Task types |

## Area → skills & rules (load when touching)

**Yaml-synced** — `agents_skill` / `agents_rules` in [docs/feature-areas.yaml](docs/feature-areas.yaml)
are parity SSOT (`sync_agents_area_table.py --check`). Signature: `governance-area-schema-agents-table-sync`.

| Area | Skill | Rule(s) |
| ---- | ----- | ------- |
| Agent / routing / self-eval | [agent-triage](.cursor/skills/agent-triage/SKILL.md), [agent-self-evaluation](.cursor/skills/agent-self-evaluation/SKILL.md), [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md), [pre-commit-workflow](.cursor/skills/pre-commit-workflow/SKILL.md), [reference](.cursor/skills/kanban-markdown/reference.md) | [agent-routing](.cursor/rules/agent-routing.mdc), [agent-self-evaluation](.cursor/rules/agent-self-evaluation.mdc), [agent-agents-md-maintenance](.cursor/rules/agent-agents-md-maintenance.mdc), [agent-consistency](.cursor/rules/agent-consistency.mdc), [kanban-card-gates](.cursor/rules/kanban-card-gates.mdc), [kanban-feature-cards](.cursor/rules/kanban-feature-cards.mdc), [kanban-bug-cards](.cursor/rules/kanban-bug-cards.mdc), [kanban-review-qa](.cursor/rules/kanban-review-qa.mdc), [kanban-commit-issue-cards](.cursor/rules/kanban-commit-issue-cards.mdc), [kanban-inquiry-cards](.cursor/rules/kanban-inquiry-cards.mdc), [kanban-plan-cards](.cursor/rules/kanban-plan-cards.mdc), [kanban-agent-cards](.cursor/rules/kanban-agent-cards.mdc), [kanban-feedback-cards](.cursor/rules/kanban-feedback-cards.mdc), [kanban-prior-lessons-gate](.cursor/rules/kanban-prior-lessons-gate.mdc), [testing](.cursor/rules/testing.mdc) |
| Kanban / `.devtool/features/` | [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md), [reference](.cursor/skills/kanban-markdown/reference.md) | [kanban-card-gates](.cursor/rules/kanban-card-gates.mdc), [kanban-feature-cards](.cursor/rules/kanban-feature-cards.mdc), [kanban-bug-cards](.cursor/rules/kanban-bug-cards.mdc), [kanban-review-qa](.cursor/rules/kanban-review-qa.mdc), [kanban-commit-issue-cards](.cursor/rules/kanban-commit-issue-cards.mdc), [kanban-inquiry-cards](.cursor/rules/kanban-inquiry-cards.mdc), [kanban-plan-cards](.cursor/rules/kanban-plan-cards.mdc), [kanban-agent-cards](.cursor/rules/kanban-agent-cards.mdc), [kanban-feedback-cards](.cursor/rules/kanban-feedback-cards.mdc), [kanban-prior-lessons-gate](.cursor/rules/kanban-prior-lessons-gate.mdc), [agent-consistency](.cursor/rules/agent-consistency.mdc), [testing](.cursor/rules/testing.mdc) |
| UI panels / dialogs | [ui-change](.cursor/skills/ui-change/SKILL.md) | [ui-panels](.cursor/rules/ui-panels.mdc), [ui-general](.cursor/rules/ui-general.mdc), [testing](.cursor/rules/testing.mdc) |
| Registry / palettes | [repo-map](.cursor/skills/repo-map/SKILL.md) | [testing](.cursor/rules/testing.mdc) |
| Structure YAML / loader | [repo-map](.cursor/skills/repo-map/SKILL.md) § Structure packages | — |
| Worldgen | [project-context](.cursor/skills/project-context/SKILL.md) | [worldgen](.cursor/rules/worldgen.mdc) |
| Tests / commit | [targeted-testing](.cursor/skills/targeted-testing/SKILL.md) | [testing](.cursor/rules/testing.mdc) |
| Docs after code | [docs-maintenance](.cursor/skills/docs-maintenance/SKILL.md) | — |
| Minecraft version facts | [project-context](.cursor/skills/project-context/SKILL.md) | — |
| Render Preview | [ui-change](.cursor/skills/ui-change/SKILL.md) | [ui-panels](.cursor/rules/ui-panels.mdc), [ui-general](.cursor/rules/ui-general.mdc), [testing](.cursor/rules/testing.mdc) |
| Floating Camera | [ui-change](.cursor/skills/ui-change/SKILL.md) | [ui-panels](.cursor/rules/ui-panels.mdc), [ui-general](.cursor/rules/ui-general.mdc), [testing](.cursor/rules/testing.mdc) |

Path→test: [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md). Hook SSOT: `scripts/pre-commit-pytest.sh`.

## Repo layout (one screen)

```text
structures/{name}/structure.yaml          # manifest
structures/{name}/stage{N}/stage.yaml     # stage + layer_files
structures/{name}/stage{N}/layers/*.yaml
ui/                                       # grep main_window.py — do not read whole file
registries/                               # behaviors, palettes, catalog
renderers/ + render_main.py               # blueprint / preview / worldgen
helpers/
.devtool/features/                        # kanban To Do (agents)
docs/feature-areas.yaml
```

## Implementation gates (kanban)

Before `in-progress` → `review` on **feature/bug/agent** cards:

- **Product** + **Tests** + **Docs** complete (no `_TBD_` at Review)
- **Prior lessons gate** + `**Prior lessons (YYYY-MM-DD):**` on card
- Staged `scripts/pre-commit-pytest.sh` green; [docs/feature-areas.yaml](docs/feature-areas.yaml) + **Docs** updated
- All **Acceptance Criteria** `[x]`

**Inquiry** → **Response** on card → `review`. **Review QA fixes:** [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § User-reported QA fixes.

**Card Done:** [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Card Done + reference §
Forward-feedback capture cadence — agent moves on QA-complete; lessons for `feature`/`bug`/`agent`/`commit-issue`.

## End handoff (required every turn)

Full template: [agent-self-evaluation](.cursor/skills/agent-self-evaluation/SKILL.md) §7 — Signature:
`governance-compact-self-eval-handoff`. **Last sections:** optional Card Done / epic blocks per §7;
then **`### Files used`** then **`### Self-evaluation`** (one line per field).

**Implementation turns:** edit **≥1 skill** and **≥1 rule** (§6).

## What not to do

- Implement product code without card + **agent verb**
- Edit on **review-only** prompt (`review @card` without update/implement/spawn)
- Card Done lessons/ff on **`inquiry`** or **`feedback`** cards
- Pick work from Backlog or `docs/roadmap.md` without user direction
- Full `pytest` after every small edit; read all of `ui/main_window.py`
- Web-search Minecraft 1.x — use [project-context](.cursor/skills/project-context/SKILL.md) (26.x)
- Skip self-evaluation, **Files used**, or dual skill+rule updates on implementation
- Python lines **> 100** chars (Ruff E501)
