# Agent guide — structure_scripts

**Start here** for Cursor agents. This repo uses **kanban cards** (`.devtool/features/`) as the primary work queue unless the user is in **Ask mode**.

Thin always-on orchestration: [`.cursor/rules/agent-routing.mdc`](.cursor/rules/agent-routing.mdc).  
Full process: [`.cursor/skills/agent-triage/SKILL.md`](.cursor/skills/agent-triage/SKILL.md) → work → [`.cursor/skills/agent-self-evaluation/SKILL.md`](.cursor/skills/agent-self-evaluation/SKILL.md).

Do **not** use [docs/roadmap.md](docs/roadmap.md) as the task queue.

## Default: kanban-first

| User mode | How work arrives | Agent does |
| --------- | ---------------- | ---------- |
| **Agent mode** (default) | To Do card path, id, title, or “implement first card” | [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) lifecycle |
| **Ask mode** | Questions only | Read-only — no card moves, no code unless user switches mode |

**Ignore Backlog** unless the user names a backlog card. **Done** column moves are **user only**.

### Card types (`labels` in frontmatter)

| Label | User provides | Agent provides before `in-progress` |
| ----- | ------------- | ------------------------------------- |
| *(feature)* | Feature Areas, story | Label Paths, **Decisions**, Acceptance Criteria |
| `bug` | Steps to Reproduce, Current/Expected Behavior, Feature Areas | Root Cause, AC, Label Paths, **Corrective Action** — [kanban-bug-cards.mdc](.cursor/rules/kanban-bug-cards.mdc) |
| `inquiry` | Description; Feature Areas optional | **Response**, Label Paths if areas set — [kanban-inquiry-cards.mdc](.cursor/rules/kanban-inquiry-cards.mdc) |

Resolve **Feature Areas** → **Label Paths** via [docs/feature-areas.yaml](docs/feature-areas.yaml):

```bash
python scripts/resolve_feature_areas.py "Render Preview"
```

## Every turn (non–Ask mode)

```text
1. Classify     → agent-triage §1 (kanban card vs surgical vs read-only)
2. Discover     → grep first; ≤3 file reads then grep/semantic search
3. Work         → Label Paths on card, or minimal surgical diff
4. Verify       → targeted pytest (scripts/pre-commit-pytest.sh on staged paths)
5. Self-eval    → handoff block; implementation: ≥1 skill + ≥1 rule updated
```

## Classify quickly

| Signal | Mode | First read |
| ------ | ---- | ---------- |
| Kanban card assigned | **Review first** → implement | Card + [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) |
| Explain / audit / “is this correct?” | **Read-only** | Grep + read only |
| One error, lint, typo, ad-hoc bug | **Surgical** | Grep → 1–3 files — no card unless user assigns one |
| Multi-file feature (no card) | **Implementation** | [repo-map](.cursor/skills/repo-map/SKILL.md) |
| Pre-commit failed | **Unblock** | [pre-commit-workflow](.cursor/skills/pre-commit-workflow/SKILL.md) |

## Area → skills & rules (load when touching)

| Area | Skill | Rule(s) |
| ---- | ----- | ------- |
| Kanban / `.devtool/features/` | [kanban-markdown](.cursor/skills/kanban-markdown/SKILL.md) | [kanban-bug-cards](.cursor/rules/kanban-bug-cards.mdc), [kanban-inquiry-cards](.cursor/rules/kanban-inquiry-cards.mdc) |
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

Before `in-progress` → `review` on **feature/bug** cards:

- Staged `scripts/pre-commit-pytest.sh` green
- [docs/feature-areas.yaml](docs/feature-areas.yaml) updated
- [docs/](docs/) reviewed per [docs-maintenance](.cursor/skills/docs-maintenance/SKILL.md)
- All **Acceptance Criteria** `[x]` on the card

**Inquiry** cards: **Response** on card → `review`; no pytest unless code also changed.

## End handoff (required every turn)

```markdown
### Self-evaluation
- **Scope:** …
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
- Skip self-evaluation or dual skill+rule updates on implementation
