# Governance overview

## Cursor agent workflow

Agent routing and kanban process live outside application code:

- [AGENTS.md](../../AGENTS.md) — entry point; **prompt verb gate** (`review` → ask-only; `implement` / `update` / `spawn` → agent); card types; Card Done agent move on QA-complete (`card-done-agent-move-qa-complete`) + lessons + **forward-looking feedback** (`card-done-forward-feedback`) scope
- [kanban-card-gates.mdc](../../.cursor/rules/kanban-card-gates.mdc) — §2 Ask-only vs Agent prompts (canonical table)
- [kanban-markdown/SKILL.md](../../.cursor/skills/kanban-markdown/SKILL.md) — card lifecycle; **prior lessons gate** before Decisions/CA; registry maintenance
- [kanban-markdown/reference.md](../../.cursor/skills/kanban-markdown/reference.md) — card templates, audit checklist, examples (load on demand; gc1); **Kanban card scope** (Product / Tests / Docs — ks0); **Cursor mode gates** (Plan / Inquire — cm0; Signature: `kanban-cursor-mode-gates`)

## Audience

| Audience | Primary reads | Does not duplicate |
| -------- | ------------- | ------------------ |
| **Human product contributor** | [development.md](../development.md), product docs | Classify tables, kanban templates, mode matrices |
| **Human governance contributor** | This handbook + yaml in `docs/` | Full skill/rule prose — follow deep links |
| **Cursor agent** | [AGENTS.md](../../AGENTS.md) → `.cursor/skills/` + rules | Long handbook prose except onboarding skim |
| **CI / scripts** | `docs/*.yaml`, parity/coverage scripts | Markdown handbooks |

## Load order

1. [AGENTS.md](../../AGENTS.md) — routing entry
2. Topic file below (kanban, lessons, parity, audit)
3. Scoped `.cursor/skills/` / `.cursor/rules/` for enforcement detail
4. Yaml registries: [feature-areas.yaml](../feature-areas.yaml), [lessons-index.yaml](../lessons-index.yaml),
   [forward-feedback-index.yaml](../forward-feedback-index.yaml)

## Handbook files

| File | Topics |
| ---- | ------ |
| [kanban-workflow.md](kanban-workflow.md) | Card scope, mode gates, prompt verbs |
| [lessons-and-coverage.md](lessons-and-coverage.md) | Lessons index, coverage metric, artifacts |
| [forward-feedback.md](forward-feedback.md) | Forward-feedback index CLI |
| [feature-areas-parity.md](feature-areas-parity.md) | Area schema, on-demand parity |
| [audit-and-compaction.md](audit-and-compaction.md) | Periodic audit, gc0 baseline |

Layout schema: [kanban-markdown/reference.md § Docs governance layout]
(../../.cursor/skills/kanban-markdown/reference.md#docs-governance-layout).
Signature: `docs-governance-split`.
