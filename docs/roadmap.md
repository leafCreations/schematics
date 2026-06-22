# Roadmap

## Design goals

* Registry-driven customization
* Modular renderer expansion
* Additional structure presets
* Advanced landscaping systems
* Desktop UI for structure authoring

## Statuses

- Not Started = Item has not been started yet
- Up Next = Item is planned but not yet started
- Planned = Item is ready for implementation and will be started soon
- In Progress = Item is currently being worked on
- Completed = Item has been completed and is ready for use

## UI

| Status | Item |
| ------ | ---- |
| Completed | Agent triage skill — [`.cursor/skills/agent-triage/SKILL.md`](../.cursor/skills/agent-triage/SKILL.md) |
| Completed | Agent repo-map skill — [`.cursor/skills/repo-map/SKILL.md`](../.cursor/skills/repo-map/SKILL.md) |
| Completed | Agent targeted-testing skill — [`.cursor/skills/targeted-testing/SKILL.md`](../.cursor/skills/targeted-testing/SKILL.md) |
| Completed | Agent pre-commit workflow skill — [`.cursor/skills/pre-commit-workflow/SKILL.md`](../.cursor/skills/pre-commit-workflow/SKILL.md) |
| Completed | Agent ui-change skill — [`.cursor/skills/ui-change/SKILL.md`](../.cursor/skills/ui-change/SKILL.md) |
| Completed | Agent self evaluation skill — [`.cursor/skills/agent-self-evaluation/SKILL.md`](../.cursor/skills/agent-self-evaluation/SKILL.md) (exit review + skill feedback loop) |
| Not Started | Add 26.2 assets. Come up with a process to avoid duplicate folder structures. |
| Not Started | Live render preview pane |
| Not Started | In-app structure metadata editing |
| Not Started | Multiple structures per site — each selectable and nudged independently on the Site tab |
| Not Started | Allow for custom mod assets |
| Not Started | Select world version to generate |


See [ui.md](ui.md) for the current editor guide.

The Site tab today assumes **one** structure per stage (`offset_x` / `offset_z` on a single layer footprint). Nudge and placement are intentionally per-footprint so a later model can register many structures (each with its own offset and layer reference) without redoing the UX.

## Future plans

* Render preview system (embedded or side-by-side with editor)
* Structure preset browser
* Theme/style packs
* Advanced terrain generation
* Multi-biome support
* Animated build progression renders
