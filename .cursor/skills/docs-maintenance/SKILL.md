---
name: docs-maintenance
description: >-
  Mandatory review and update of docs/ after implementation, kanban cards, UI,
  render pipeline, registry, or workflow changes. Use before kanban in-progress →
  review, before commit-ready handoff on code changes, or when the user asks to
  sync documentation. No exceptions — agents must grep docs/ for stale content
  and update every affected file in the same turn.
---

# Docs maintenance

**Hard constraint:** after **any code change** that ships behavior, paths, or user-facing workflow, the agent **MUST** review and update `docs/` in the **same turn** before:

- moving a kanban card to **Review**
- claiming **Commit-ready: yes**
- ending an implementation or QA-fix turn

**No exceptions** — not for “small” diffs, not for “internal only”, not deferred to a follow-up turn. Read-only Q&A turns do not edit docs unless the user asks to fix incorrect documentation.

Pair with [kanban-markdown](../kanban-markdown/SKILL.md) (`docs/feature-areas.yaml`) and [ui-change](../ui-change/SKILL.md) (UI surfaces).

## When mandatory

| Work type | Docs pass required? |
| --------- | ------------------- |
| Kanban implementation or QA Review fix | **Yes** — full pass |
| Surgical bug fix in `ui/`, `renderers/`, `registries/`, `helpers/` with behavior change | **Yes** |
| Ad-hoc feature/refactor touching listed areas below | **Yes** |
| Test-only, comment-only, or `.cursor/` skill/rule edits | No — unless behavior docs would be wrong |
| Pure read-only explanation | No edits — cite current docs; flag staleness if found |

## Process (every mandatory pass)

1. **List changed paths** (from card Label Paths, diff, or task scope).
2. **Map** changed areas → doc files (table below). Include **`docs/feature-areas.yaml`** for kanban/feature work (see kanban skill).
3. **Grep** `docs/` for stale terms tied to the change (old tab names, removed controls, wrong output paths, “not yet implemented”, obsolete workflows).
4. **Update every affected file** — minimal accurate diffs; match existing doc tone.
5. **Handoff** — self-evaluation must include **Docs:** with paths updated or `n/a` + one-line why.

```bash
# Stale-term sweep examples (adjust terms to the feature)
rg -i 'Render tab|Generate Renders|no embedded preview' docs/
rg -i 'Viewer tab|Materials List|_preview' docs/
```

## Change → doc map

| Changed area | Review / update (all that apply) |
| ------------ | -------------------------------- |
| `ui/` — tabs, panels, menus, dialogs, shortcuts | [ui.md](../../docs/ui.md), [structure-editor-guide.md](../../docs/structure-editor-guide.md), [editor-properties.md](../../docs/editor-properties.md), [ui-panel-refactor.md](../../docs/ui-panel-refactor.md) (panel map) |
| `renderers/`, `render_main.py`, `ui/render_preview.py`, preview/export | [render-types.md](../../docs/render-types.md), [ui.md](../../docs/ui.md) (Viewer tab), [structure-editor-guide.md](../../docs/structure-editor-guide.md) |
| `registries/`, palettes, catalog, tokens | [registry.md](../../docs/registry.md), [structure-tokens.md](../../docs/structure-tokens.md) |
| Structure package layout / loader | [structure-tokens.md](../../docs/structure-tokens.md), [project-structure.md](../../docs/project-structure.md) |
| Worldgen | [worldgen.md](../../docs/worldgen.md), [project-info.md](../../docs/project-info.md) if version targets change |
| Sprite baker / block icons | [sprite-baker.md](../../docs/sprite-baker.md), [assets.md](../../docs/assets.md) |
| Dev setup, pytest, pre-commit | [development.md](../../docs/development.md) |
| Kanban feature areas, new modules/tests | [feature-areas.yaml](../../docs/feature-areas.yaml) — **mandatory** per kanban skill |
| Shipped roadmap-scale capability | [roadmap.md](../../docs/roadmap.md) — mark completed / remove “not yet” claims; **do not** add new queue items (kanban is the queue) |

**UI tab naming:** the editor tab label is **Viewer**; kanban/feature registry may still use **Render Tab** as the product-area label — keep both consistent in prose (see materials-list QA).

## What to fix when reviewing

- User workflow steps match current controls (dropdown vs checkboxes, button names, menu paths).
- Output paths and preview session dir (`output/schematics/_preview/{session}/`) match code.
- “Implemented” vs “Not yet” lists in [ui.md](../../docs/ui.md) and [roadmap.md](../../docs/roadmap.md) reflect reality.
- [editor-properties.md](../../docs/editor-properties.md) tables match panel controls and save targets.
- No duplicate contradictory guidance across user guide vs developer reference — update both when behavior is user-visible.

## Do not

- Invent features not in code.
- Document speculative work as shipped.
- Update [roadmap.md](../../docs/roadmap.md) as the agent task queue (use kanban).
- Skip docs because tests pass or the card AC does not mention docs.
- Leave “update docs later” in the handoff.

## Related skills

| Skill | Role |
| ----- | ---- |
| [kanban-markdown](../kanban-markdown/SKILL.md) | `feature-areas.yaml` + AC before Review |
| [ui-change](../ui-change/SKILL.md) | UI wiring checklist |
| [agent-triage](../agent-triage/SKILL.md) | Routes implementation work here |
| [agent-self-evaluation](../agent-self-evaluation/SKILL.md) | **Docs:** line in handoff |
| [repo-map](../repo-map/SKILL.md) | Subsystem → doc entry points |
