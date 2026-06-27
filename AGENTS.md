# Agent guide — structure_scripts

**Start here** for Cursor agents. **Agent mode** requires a kanban card, valid `labels`, and an **agent verb** (`implement`, `update`, `spawn`, …) — see [kanban-card-gates.mdc](.cursor/rules/kanban-card-gates.mdc). **`review …` only** or no card → **Ask-only** (read-only).

Thin always-on orchestration: [`.cursor/rules/agent-routing.mdc`](.cursor/rules/agent-routing.mdc).  
Full process: [`.cursor/skills/agent-triage/SKILL.md`](.cursor/skills/agent-triage/SKILL.md) → work → [`.cursor/skills/agent-self-evaluation/SKILL.md`](.cursor/skills/agent-self-evaluation/SKILL.md).

Do **not** use [docs/roadmap.md](docs/roadmap.md) as the task queue.

## Default: kanban-first

| User mode | How work arrives | Agent does |
| --------- | ---------------- | ---------- |
| **Agent mode** | Card named + **agent verb** (`implement`, `update`, `review and update`, `spawn`, `answer inquiry`, …) | [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md); [kanban-card-gates.mdc](.cursor/rules/kanban-card-gates.mdc) §2 |
| **Ask-only** | `review …` card only, bare `@path`, no card, or prompt without agent verb | Read-only — no file edits; suggest upgrade to `review and update` / `implement` |
| **Governance lessons epics** | `ArtifactsDocYaml`, `LessonsCoverageMetric`, `GovernanceAreaSchema` | Read **To Do + Backlog**; sort by `order` — [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Reading the board |

**Ignore Backlog** unless the user names a backlog card. **Done** column moves are **user only**.

**No implementation without a card** — no surgical/ad-hoc fixes.

### Card label gate

Every card **must** have a recognized `labels` entry (inline JSON array). **Invalid** (missing, `labels: []`, unknown) → **stop**; user must set `feature`, `bug`, `agent`, `inquiry`, or `commit-issue`.

### Card types (`labels` in frontmatter)

| Label | User provides | Agent provides before `in-progress` |
| ----- | ------------- | ------------------------------------- |
| `feature` | Feature Areas, story | Label Paths, **Label Methods**, **Decisions**, AC — [kanban-feature-cards.mdc](.cursor/rules/kanban-feature-cards.mdc) |
| `bug` | Steps to Reproduce, Current/Expected Behavior, Feature Areas | Root Cause, AC, Label Paths, **Label Methods**, **Corrective Action** — [kanban-bug-cards.mdc](.cursor/rules/kanban-bug-cards.mdc) |
| `commit-issue` | _(auto)_ Problem + Failed Tests | **Review:** Root Cause + Corrective Action; optional Label Paths / Label Methods; implement after user approval — [kanban-commit-issue-cards.mdc](.cursor/rules/kanban-commit-issue-cards.mdc) |
| `inquiry` | Description; Feature Areas optional | **Response**, Label Paths, **Label Methods** (when set); spawn child cards when user approves — [kanban-inquiry-cards.mdc](.cursor/rules/kanban-inquiry-cards.mdc); **no** Card Done lessons |
| `agent` | **Description**, **Feature Area** (default `Agent Workflow`) | Label Paths, **Label Methods**, **Acceptance Criteria**, **Decisions** — [kanban-agent-cards.mdc](.cursor/rules/kanban-agent-cards.mdc) |

Resolve **Feature Areas** → **Label Paths** + **Label Methods** via [docs/feature-areas.yaml](docs/feature-areas.yaml):

```bash
python scripts/resolve_feature_areas.py "Render Preview"
python scripts/resolve_feature_areas.py --handlers "Open Structures Workflow"
python scripts/resolve_feature_areas.py --lessons "Render Preview"
```

## Every turn (non–Ask mode)

```text
1. Classify     → reference § Classify (+ AGENTS summary; triage §1 — kanban card + label gate → one scoped kanban-*-cards.mdc)
1b. On failure  → agent-triage §1b grep reference.md tables (signals only — not every turn)
2. Discover     → grep first; ≤3 file reads then grep/semantic search
3. Work         → kanban: Label Paths + Label Methods → prior lessons gate → Decisions/CA
                  → Review QA fix: append **QA follow-up**; refresh Feature Areas / Label Paths /
                    Label Methods when fix scope changes (kanban-markdown § User-reported QA fixes)
4. Verify       → ruff E501 on touched `.py` (`.venv/bin/ruff check --select E501` — Signature:
                  `ruff-e501-line-length`); targeted pytest (scripts/pre-commit-pytest.sh on staged paths)
5. Done signal  → user says card Done → **lessons learned** + **forward-looking feedback** for
                    `feature` / `bug` / `agent` / `commit-issue` (kanban-markdown § Card Done;
                    Signature: `card-done-forward-feedback`; top-3 in chat before handoff);
                    **`inquiry` → neither**
                  → `python3 scripts/build_lessons_index.py` when lessons ran;
                    curate area `lesson_*` keys when new Signatures/docs apply (`--sync-registry` dry-run)
6. Self-eval    → Files used (load order) + handoff; implementation: ≥1 skill + ≥1 rule updated;
                  audit AGENTS.md freshness; governance edits → self-eval §6g
```

## Maintaining AGENTS.md (routing guide)

**Agents MUST evaluate this file every turn** (self-evaluation §2b check 4). Update **AGENTS.md** in the same turn when you add or change:

| Change in repo | Update in AGENTS.md |
| -------------- | ------------------- |
| Feature Areas → Label Paths + Label Methods workflow | Every turn step 3; card types table; `resolve_feature_areas.py --handlers` example |
| New kanban label type (`commit-issue`, …) | Card types table + area→rules row |
| New area skill or scoped rule | Area → skills & rules table |
| New turn step, gate, or script workflow | Every turn / Classify quickly / Implementation gates |
| Lessons-by-area routing (li3) | AGENTS Classify **Area lesson lookup** + triage §1/§2 + reference § Lessons by area + kanban-prior-lessons-gate read order |
| Kanban pre-implementation / prior lessons gate | Every turn step 3; Classify quickly; [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Prior lessons gate + [kanban-prior-lessons-gate.mdc](.cursor/rules/kanban-prior-lessons-gate.mdc); `scripts/resolve_prior_lessons.py` (scans `done/` + `archived/`); `docs/lessons-index.yaml` via `scripts/build_lessons_index.py` (refresh after Card Done); [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § Lessons by area (read before done-card grep); optional `artifacts:` tail on lesson bullets — [docs/development.md](docs/development.md) § Lessons captured `artifacts:` schema |
| Kanban prompt verb gate | Classify quickly; Every turn step 1; [kanban-card-gates.mdc](.cursor/rules/kanban-card-gates.mdc) §2; kanban-markdown § Ask-only vs Agent prompts |
| Kanban card label gate / no-card implementation | Classify quickly; Every turn step 1; card types table; What not to do |
| Card Done lessons label scope (`feature`/`bug`/`agent` vs `inquiry`) | Every turn step 5; Implementation gates; Classify quickly Done rows |
| Card Done forward-looking feedback (`card-done-forward-feedback`) | Every turn step 5; kanban-markdown § Card Done; top-3 chat (`### Top forward feedback`); kanban-review-qa.mdc; scoped kanban-*.mdc Card Done sections |
| Kanban Review QA record / Done lessons capture | Every turn steps 3–5; [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § User-reported QA fixes + § Card Done |
| Failure-pattern routing (triage §1b) | Every turn step 1b + Classify quickly + [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) |
| Classify SSOT (gc2) | Full table in [reference.md](.cursor/skills/agent-triage/reference.md) § Classify only; AGENTS ≤5-row summary; triage §1 pointer; `check_classify_parity` — Signature: `governance-compact-classify-ssot` |
| Classify task types (gc6) | reference.md § Task types + triage §2 Task types summary; Signature: `governance-compact-classify-task-types` |
| Kanban rule globs (gc3) | triage §1 pointer to agent-routing § Kanban card type; `check_kanban_rule_globs`; docs/development.md § Governance compaction — Signature: `governance-compact-kanban-rule-globs` |
| Lessons coverage drift / `check_governance_parity.py` lessons integration | Classify quickly + triage §1 + [docs/development.md](docs/development.md) § Lessons Coverage Metric |
| Governance audit Classify row | Classify quickly + agent-triage §1 + [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Periodic AGENTS.md governance audit |
| Kanban Label Methods gate | Card types table + [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Feature Areas |
| Handoff format fields | End handoff section |
| Failure pattern schema or new cross-cutting row | Classify quickly (failure-pattern lookup) + [agent-self-evaluation/reference.md](.cursor/skills/agent-self-evaluation/reference.md) |
| New scoped **agent/kanban rule** | Area → skills & rules table + [agent-consistency.mdc](.cursor/rules/agent-consistency.mdc) checklist if governance paths |
| Governance area schema keys (`agents_skill`, `agents_rules`, `lesson_routing_row`) | `docs/feature-areas.yaml` header + [docs/development.md](docs/development.md) § Governance area schema — gs4 sync via `scripts/sync_agents_area_table.py` — Signature: `governance-area-schema-agents-table-sync` |
| Governance artifact parity (any agent/kanban edit) | [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § Consistency matrix |
| Drift alert vocabulary (prefix lines) | [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § Drift alert examples |
| Drift severity + KNOWN_DRIFT format | [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § Drift severity, § KNOWN_DRIFT |
| Drift alert surfacing (Context load / §6g / handoff) | [agent-self-evaluation/SKILL.md](.cursor/skills/agent-self-evaluation/SKILL.md) §2b check 5 + §6g; [agent-triage/SKILL.md](.cursor/skills/agent-triage/SKILL.md) § Governance drift detection |

If behavior changed but **AGENTS.md** still describes the old flow → handoff **Context load:** `AGENTS.md stale: …` and fix before closing the task when possible.

**Scoped rules:** editing `.cursor/skills/agent-*/` or `.cursor/skills/kanban-*/` → [agent-agents-md-maintenance.mdc](.cursor/rules/agent-agents-md-maintenance.mdc). Any governance path in [agent-consistency.mdc](.cursor/rules/agent-consistency.mdc) `globs` → [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § **Consistency matrix** + four check types + self-eval §6g.

**Periodic audit:** quarterly suggested — `python3 scripts/create_governance_audit_card.py` then [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Periodic AGENTS.md governance audit. **On-demand:** `python3 scripts/check_governance_parity.py` between audits (spawns **todo** fix cards per new drift issue, epic `GovernanceDriftAlert`, unless `--no-spawn-cards`).

**Drift alerts (governance edits):** when this turn edits [agent-consistency.mdc](.cursor/rules/agent-consistency.mdc) `globs` and parity is not fixed same turn, surface lines in **Context load**, **§6g**, and handoff `- **Drift alerts:**` — prefixes in [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § **Drift alert examples**; optional `[info|warn|critical]` (default `warn`); temporary waiver: `KNOWN_DRIFT: <pair> — <reason>[; expires: …]` per reference § KNOWN_DRIFT. Not on every turn.

## Files used + self-evaluation (every turn)

End every response with two sections (see [agent-self-evaluation](.cursor/skills/agent-self-evaluation/SKILL.md) §7):

1. **`### Files used`** — ordered paths/skills with role tags (`grep`, `read`, `edit`)
2. **`### Self-evaluation`** — includes **Context load** (four checks) and **AGENTS.md** current/stale/updated

## Classify quickly

**Full signal table:** [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § **Classify the request (signals)** — Signature: `governance-compact-classify-ssot`. Edit signals in reference only; summary below (≤5 rows).

| Signal | Mode | First read |
| ------ | ---- | ---------- |
| **Review** kanban card only (`review …`, bare `@path`) | **Ask-only** | Card + [kanban-card-gates](.cursor/rules/kanban-card-gates.mdc) §2 — chat only, no edits |
| **Update / spawn / implement** card (agent verbs) | **Agent** | Card + valid `labels`; [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md); prior lessons gate |
| Card missing / empty / unknown `labels` | **Block** | [kanban-card-gates](.cursor/rules/kanban-card-gates.mdc) — stop; user must set valid `labels` |
| Implement / fix / refactor **without** a card | **Ask-only** | No product edits — user must assign or create a kanban card |
| All other signals (failure, verify, governance, lessons, task type) | *see reference* | [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § Classify + § Task types |

## Area → skills & rules (load when touching)

**Yaml-synced routing table** — **gs4 complete** (`AgentsTableSync` epic). Per-area
`agents_skill` / `agents_rules` in `docs/feature-areas.yaml` are the **parity source of truth**
(`check_area_schema_parity`, `--agents-parity`, `sync_agents_area_table.py --check`). Narrative-only
rows below (Structure, Worldgen, Tests, …) stay manual. Signature:
`governance-area-schema-agents-table-sync`.

| Area | Skill | Rule(s) |
| ---- | ----- | ------- |
| Agent / routing / self-eval | [agent-triage](.cursor/skills/agent-triage/SKILL.md), [agent-self-evaluation](.cursor/skills/agent-self-evaluation/SKILL.md), [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md), [pre-commit-workflow](.cursor/skills/pre-commit-workflow/SKILL.md), [reference](.cursor/skills/kanban-markdown/reference.md) | [agent-routing](.cursor/rules/agent-routing.mdc), [agent-self-evaluation](.cursor/rules/agent-self-evaluation.mdc), [agent-agents-md-maintenance](.cursor/rules/agent-agents-md-maintenance.mdc), [agent-consistency](.cursor/rules/agent-consistency.mdc), [kanban-card-gates](.cursor/rules/kanban-card-gates.mdc), [kanban-feature-cards](.cursor/rules/kanban-feature-cards.mdc), [kanban-bug-cards](.cursor/rules/kanban-bug-cards.mdc), [kanban-review-qa](.cursor/rules/kanban-review-qa.mdc), [kanban-commit-issue-cards](.cursor/rules/kanban-commit-issue-cards.mdc), [kanban-inquiry-cards](.cursor/rules/kanban-inquiry-cards.mdc), [kanban-agent-cards](.cursor/rules/kanban-agent-cards.mdc), [kanban-prior-lessons-gate](.cursor/rules/kanban-prior-lessons-gate.mdc), [testing](.cursor/rules/testing.mdc) |
| Kanban / `.devtool/features/` | [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md), [reference](.cursor/skills/kanban-markdown/reference.md) | [kanban-card-gates](.cursor/rules/kanban-card-gates.mdc), [kanban-feature-cards](.cursor/rules/kanban-feature-cards.mdc), [kanban-bug-cards](.cursor/rules/kanban-bug-cards.mdc), [kanban-review-qa](.cursor/rules/kanban-review-qa.mdc), [kanban-commit-issue-cards](.cursor/rules/kanban-commit-issue-cards.mdc), [kanban-inquiry-cards](.cursor/rules/kanban-inquiry-cards.mdc), [kanban-agent-cards](.cursor/rules/kanban-agent-cards.mdc), [kanban-prior-lessons-gate](.cursor/rules/kanban-prior-lessons-gate.mdc), [agent-consistency](.cursor/rules/agent-consistency.mdc), [testing](.cursor/rules/testing.mdc) |
| UI panels / dialogs | [ui-change](.cursor/skills/ui-change/SKILL.md) | [ui-panels](.cursor/rules/ui-panels.mdc), [ui-general](.cursor/rules/ui-general.mdc), [testing](.cursor/rules/testing.mdc) |
| Registry / palettes | [repo-map](.cursor/skills/repo-map/SKILL.md) | [testing](.cursor/rules/testing.mdc) |
| Structure YAML / loader | [repo-map](.cursor/skills/repo-map/SKILL.md) § Structure packages | — |
| Worldgen | [project-context](.cursor/skills/project-context/SKILL.md) | [worldgen](.cursor/rules/worldgen.mdc) |
| Tests / commit | [targeted-testing](.cursor/skills/targeted-testing/SKILL.md) | [testing](.cursor/rules/testing.mdc) |
| Docs after code | [docs-maintenance](.cursor/skills/docs-maintenance/SKILL.md) | — |
| Minecraft version facts | [project-context](.cursor/skills/project-context/SKILL.md) | — |
| Render Preview | [ui-change](.cursor/skills/ui-change/SKILL.md) | [ui-panels](.cursor/rules/ui-panels.mdc), [ui-general](.cursor/rules/ui-general.mdc), [testing](.cursor/rules/testing.mdc) |

Path→test map: [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md). Hook source of truth: `scripts/pre-commit-pytest.sh`.

## Repo layout (one screen)

```text
structures/{name}/structure.yaml          # manifest — site settings save target
structures/{name}/stage{N}/stage.yaml   # stage identity + layer_files
structures/{name}/stage{N}/layers/*.yaml
ui/                                     # PySide6 editor (grep main_window.py — do not read whole file)
registries/                             # behaviors, palettes, catalog
renderers/ + render_main.py             # blueprint / preview / worldgen
helpers/                                # shared logic
.devtool/features/                      # kanban queue (To Do only for agents)
docs/feature-areas.yaml                 # Feature Areas → paths registry
```

Obsolete: `structures/{name}/stage{N}/structure.yaml`.

## Implementation gates (kanban)

Before `in-progress` → `review` on **feature/bug/agent** cards:

- **Prior lessons gate** run; `**Prior lessons (YYYY-MM-DD):**` on card ([kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Prior lessons gate)
- Staged `scripts/pre-commit-pytest.sh` green
- [docs/feature-areas.yaml](docs/feature-areas.yaml) updated
- [docs/](docs/) reviewed per [docs-maintenance](.cursor/skills/docs-maintenance/SKILL.md)
- All **Acceptance Criteria** `[x]` on the card

**Inquiry** cards: **Response** on card → `review`; no pytest unless code also changed.

**Inquiry → feature spawn:** when the user asks to implement inquiry recommendations, create **todo** feature cards per [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Spawn from inquiry — `epic: "{EpicName}"`, **Acceptance Criteria**, **Label Paths**, **Label Methods**, **Decisions**, **Context**; link from parent **`## Spawned feature cards`**. Example epics: `DesignFailureMemorySystem` (three phases); `GovernanceDriftAlerts` (four phases); `LessonsCoverageMetric` (lc0–lc3); `LessonsReferenceIndex` (li0–li3); `GovernanceAreaSchema` (gs0–gs3); `ArtifactsDocYaml` (ap0–ap1).

**Review QA fixes:** when the user reports issues during **Review**, implement fixes, append dated `**QA follow-up**` bullets on the card, and **refresh `## Feature Areas` / `## Label Paths` / `## Label Methods`** when the fix touches scope not already listed ([kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § User-reported QA fixes; [kanban-review-qa](.cursor/rules/kanban-review-qa.mdc)).

**Card Done (user):** when the user says a **`feature` / `bug` / `agent` / `commit-issue`** card is
**Done**, capture lessons in **≥1 skill**, **≥1 rule**, and relevant **docs** / registry, then add
**`## Forward-looking feedback`** on the card (Signature: `card-done-forward-feedback`); surface
top 3 items in chat (`### Top forward feedback` before handoff).
**`inquiry` Done → no lessons or forward feedback.** User moves file to `done/`; agent does not.

## End handoff (required every turn)

Full template: [agent-self-evaluation](.cursor/skills/agent-self-evaluation/SKILL.md) §7 — Signature:
`governance-compact-self-eval-handoff`. **Last sections:** `### Files used` (load order) then
`### Self-evaluation` (one line per field — expand only on failure).

**Implementation turns:** edit **≥1 skill** and **≥1 rule** (§6); read-only →
`Skills updated` / `Rules updated`: `none (read-only)`.

## What not to do

- Implement product code without card + **agent verb**
- Edit files on **review-only** prompt (`review @card` without update/implement/spawn)
- Work on a card with missing, empty, or unknown `labels` — stop and ask user to fix frontmatter
- Run Card Done lessons capture or forward feedback on **`inquiry`** cards
- Pick work from Backlog or `docs/roadmap.md` without user direction
- Full `pytest` after every small edit (use targeted tests)
- Read all of `ui/main_window.py` — grep handlers first
- Web-search Minecraft 1.x facts — use [project-context](.cursor/skills/project-context/SKILL.md) (26.x)
- Skip self-evaluation, **Files used**, or dual skill+rule updates on implementation
- Write Python lines longer than **100** characters (Ruff E501; wrap strings and split long expressions)
