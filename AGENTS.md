# Agent guide — structure_scripts

**Start here** for Cursor agents. This repo uses **kanban cards** (`.devtool/features/`) as the primary work queue unless the user is in **Ask mode**.

Thin always-on orchestration: [`.cursor/rules/agent-routing.mdc`](.cursor/rules/agent-routing.mdc).  
Full process: [`.cursor/skills/agent-triage/SKILL.md`](.cursor/skills/agent-triage/SKILL.md) → work → [`.cursor/skills/agent-self-evaluation/SKILL.md`](.cursor/skills/agent-self-evaluation/SKILL.md).

Do **not** use [docs/roadmap.md](docs/roadmap.md) as the task queue.

## Default: kanban-first

| User mode | How work arrives | Agent does |
| --------- | ---------------- | ---------- |
| **Agent mode** (default) | To Do card path, id, title, or “implement first card” | [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) lifecycle |
| **Governance lessons epics** | `ArtifactsDocYaml`, `LessonsCoverageMetric`, `GovernanceAreaSchema` | Read **To Do + Backlog**; sort by `order` (`a0`–`a9` queue) — [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Reading the board |
| **Ask mode** | Questions only | Read-only — no card moves, no code unless user switches mode |

**Ignore Backlog** unless the user names a backlog card. **Done** column moves are **user only**.

### Card types (`labels` in frontmatter)

| Label | User provides | Agent provides before `in-progress` |
| ----- | ------------- | ------------------------------------- |
| *(feature)* | Feature Areas, story | Label Paths, **Label Methods**, **Decisions**, Acceptance Criteria |
| `bug` | Steps to Reproduce, Current/Expected Behavior, Feature Areas | Root Cause, AC, Label Paths, **Label Methods**, **Corrective Action** — [kanban-bug-cards.mdc](.cursor/rules/kanban-bug-cards.mdc) |
| `commit-issue` | _(auto)_ Problem + Failed Tests | **Review:** Root Cause + Corrective Action; optional Label Paths / Label Methods; implement after user approval — [kanban-commit-issue-cards.mdc](.cursor/rules/kanban-commit-issue-cards.mdc) |
| `inquiry` | Description; Feature Areas optional | **Response**, Label Paths, **Label Methods** (when Feature Areas set); **spawn:** todo feature cards + `epic` when user approves recommendations — [kanban-inquiry-cards.mdc](.cursor/rules/kanban-inquiry-cards.mdc) |
| `agent` | **Description**, **Feature Area** (default `Agent Workflow`) | Label Paths, **Label Methods**, **Acceptance Criteria**, **Decisions** — [kanban-agent-cards.mdc](.cursor/rules/kanban-agent-cards.mdc) |

Resolve **Feature Areas** → **Label Paths** + **Label Methods** via [docs/feature-areas.yaml](docs/feature-areas.yaml):

```bash
python scripts/resolve_feature_areas.py "Render Preview"
python scripts/resolve_feature_areas.py --handlers "Open Structures Workflow"
python scripts/resolve_feature_areas.py --lessons "Render Preview"
```

## Every turn (non–Ask mode)

```text
1. Classify     → agent-triage §1 (kanban card vs surgical vs read-only)
1b. On failure  → agent-triage §1b grep reference.md tables (signals only — not every turn)
2. Discover     → grep first; ≤3 file reads then grep/semantic search
3. Work         → kanban: Label Paths + Label Methods → prior lessons gate → Decisions/CA
                  → Review QA fix: append **QA follow-up**; refresh Feature Areas / Label Paths /
                    Label Methods when fix scope changes (kanban-markdown § User-reported QA fixes)
4. Verify       → targeted pytest (scripts/pre-commit-pytest.sh on staged paths)
5. Done signal  → user says card Done → lessons learned capture (kanban-markdown § Card Done)
                  → `python3 scripts/build_lessons_index.py` refresh `docs/lessons-index.yaml`;
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
| Kanban Review QA record / Done lessons capture | Every turn steps 3–5; [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § User-reported QA fixes + § Card Done |
| Failure-pattern routing (triage §1b) | Every turn step 1b + Classify quickly + [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) |
| Classify quickly parity | Classify quickly ↔ triage §1 ↔ [reference.md](.cursor/skills/agent-triage/reference.md) § Classify — update all three when adding a signal row (including **Verify**: `run tests` / `commit-ready`) |
| Governance audit Classify row | Classify quickly + agent-triage §1 + [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Periodic AGENTS.md governance audit |
| Kanban Label Methods gate | Card types table + [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Feature Areas |
| Handoff format fields | End handoff section |
| Failure pattern schema or new cross-cutting row | Classify quickly (failure-pattern lookup) + [agent-self-evaluation/reference.md](.cursor/skills/agent-self-evaluation/reference.md) |
| New scoped **agent/kanban rule** | Area → skills & rules table + [agent-consistency.mdc](.cursor/rules/agent-consistency.mdc) checklist if governance paths |
| Governance area schema keys (`agents_skill`, `agents_rules`, `lesson_routing_row`) | `docs/feature-areas.yaml` header + [docs/development.md](docs/development.md) § Governance area schema — **gs0–gs3 complete**; **do not** sync **Area → skills & rules** table from yaml until a separate follow-up epic |
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

| Signal | Mode | First read |
| ------ | ---- | ---------- |
| Kanban card assigned | **Review first** → implement | Card + [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md); **prior lessons gate** before Decisions/CA |
| Review QA issue (chat/screenshot) | **Surgical** / **Review** | Fix + **QA follow-up** + refresh **Feature Areas** / **Label Paths** / **Label Methods** — [kanban-review-qa](.cursor/rules/kanban-review-qa.mdc) |
| User says card **Done** | **Governance** | [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Card Done — lessons learned |
| AGENTS.md governance audit card | **Read-only** | [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Periodic AGENTS.md governance audit; card from `scripts/create_governance_audit_card.py` → **## Audit findings** → `review` (no fixes unless asked) |
| Explain / audit / “is this correct?” | **Read-only** | Grep + read only |
| One error, lint, typo, ad-hoc bug | **Surgical** | Grep → 1–3 files — no card unless user assigns one |
| Multi-file feature (no card) | **Implementation** | [repo-map](.cursor/skills/repo-map/SKILL.md) |
| Pre-commit failed | **Unblock** / **Review** | §1b failure-pattern grep → [pre-commit-workflow](.cursor/skills/pre-commit-workflow/reference.md) + [agent-self-evaluation/reference.md](.cursor/skills/agent-self-evaluation/reference.md); then [pre-commit-workflow/SKILL.md](.cursor/skills/pre-commit-workflow/SKILL.md); `commit-issue` card if capture ran; mass ruff in `site-packages` → `precommit-ruff-staged-venv` |
| Agent created `.tmp-venv` / pytest without `.venv` | **Surgical** | §1b `agent-no-tmp-venv` → [targeted-testing](.cursor/skills/targeted-testing/SKILL.md); ask user to set up `.venv` |
| Failing test / pytest / ruff / lint | **Surgical** or **Unblock** | §1b grep → [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § Failure pattern routing |
| UI wiring / dialog not persisting | **Surgical** | §1b grep `ui-dialog-no-persist` → [ui-change](.cursor/skills/ui-change/SKILL.md) |
| Orbit 3D holes / transparent partial blocks | **Surgical** | §1b `orbit-stair-mask-transparency` → [ui-change](.cursor/skills/ui-change/SKILL.md) § Orbit lessons; `test_orbit_stair_face_textures_are_opaque` |
| Agent handoff / kanban / process mistake | **Surgical** | §1b grep → [agent-self-evaluation/reference.md](.cursor/skills/agent-self-evaluation/reference.md) § Common failure patterns |
| Repeated mistake / familiar churn | **Grep** | Same tables as §1b — [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § Failure pattern routing |
| "Run tests" / verify / commit-ready | **Verify** | [targeted-testing](.cursor/skills/targeted-testing/SKILL.md); `scripts/pre-commit-pytest.sh` on staged files → optional `record-pytest-pass.sh` |
| Area lesson lookup (kanban + Feature Areas) | **Review first** | `docs/lessons-index.yaml` area block + [agent-triage/reference.md](.cursor/skills/agent-triage/reference.md) § Lessons by area → `resolve_prior_lessons.py` |

## Area → skills & rules (load when touching)

**Narrative routing table** — **gs0–gs3 complete** (`GovernanceAreaSchema` epic). Per-area `agents_skill` / `agents_rules` in `docs/feature-areas.yaml` are the **parity source of truth** (`check_area_schema_parity`, `--agents-parity`). This table stays narrative until a follow-up epic syncs or generates rows from yaml (Signature: `governance-area-schema-defer-agents-table`).

| Area | Skill | Rule(s) |
| ---- | ----- | ------- |
| Agent / routing / self-eval | [agent-triage](.cursor/skills/agent-triage/SKILL.md), [agent-self-evaluation](.cursor/skills/agent-self-evaluation/SKILL.md), [pre-commit-workflow](.cursor/skills/pre-commit-workflow/SKILL.md) | [agent-routing](.cursor/rules/agent-routing.mdc), [agent-self-evaluation](.cursor/rules/agent-self-evaluation.mdc), [agent-agents-md-maintenance](.cursor/rules/agent-agents-md-maintenance.mdc), [agent-consistency](.cursor/rules/agent-consistency.mdc) |
| Kanban / `.devtool/features/` | [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) | [kanban-bug-cards](.cursor/rules/kanban-bug-cards.mdc), [kanban-review-qa](.cursor/rules/kanban-review-qa.mdc), [kanban-commit-issue-cards](.cursor/rules/kanban-commit-issue-cards.mdc), [kanban-inquiry-cards](.cursor/rules/kanban-inquiry-cards.mdc), [kanban-agent-cards](.cursor/rules/kanban-agent-cards.mdc), [kanban-prior-lessons-gate](.cursor/rules/kanban-prior-lessons-gate.mdc) |
| UI panels / dialogs | [ui-change](.cursor/skills/ui-change/SKILL.md) | [ui-panels](.cursor/rules/ui-panels.mdc), [ui-dialogs](.cursor/rules/ui-dialogs.mdc), [ui-general](.cursor/rules/ui-general.mdc) |
| Registry / palettes | [repo-map](.cursor/skills/repo-map/SKILL.md) | — |
| Structure YAML / loader | [repo-map](.cursor/skills/repo-map/SKILL.md) § Structure packages | — |
| Worldgen | [project-context](.cursor/skills/project-context/SKILL.md) | [worldgen](.cursor/rules/worldgen.mdc) |
| Tests / commit | [targeted-testing](.cursor/skills/targeted-testing/SKILL.md) | [testing](.cursor/rules/testing.mdc) |
| Docs after code | [docs-maintenance](.cursor/skills/docs-maintenance/SKILL.md) | — |
| Minecraft version facts | [project-context](.cursor/skills/project-context/SKILL.md) | — |

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

**Card Done (user):** when the user says a card is **Done**, capture lessons in **≥1 skill**, **≥1 rule**, and relevant **docs** / registry ([kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) § Card Done — lessons learned). User moves file to `done/`; agent does not.

## End handoff (required every turn)

```markdown
### Files used
1. `AGENTS.md` — …
2. …

### Self-evaluation
- **Scope:** …
- **Context load:** … — AGENTS.md <current | updated | stale: …>
- **Tests:** …
- **Docs:** …
- **Skills used:** …
- **Skills updated:** …
- **Rules updated:** …
- **Commit-ready:** …
```

**Implementation turns:** edit **≥1 skill** and **≥1 rule** — see [agent-self-evaluation](.cursor/skills/agent-self-evaluation/SKILL.md) §6.

## What not to do

- Pick work from Backlog or `docs/roadmap.md` without user direction
- Full `pytest` after every small edit (use targeted tests)
- Read all of `ui/main_window.py` — grep handlers first
- Web-search Minecraft 1.x facts — use [project-context](.cursor/skills/project-context/SKILL.md) (26.x)
- Skip self-evaluation, **Files used**, or dual skill+rule updates on implementation
- Write Python lines longer than **100** characters (Ruff E501; wrap strings and split long expressions)
