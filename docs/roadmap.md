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
- In Progress = Item is currently being worked on
- Completed = Item has been completed and is ready for use

## UI (in progress)

| Status | Item |
| ------ | ---- |
| Up Next  | Create a new skill to help agent with decision making to limit token use. |
| Not Started | Live render preview pane |
| Not Started | In-app structure metadata editing |
| Not Started | Multiple structures per site — each selectable and nudged independently on the Site tab |
| Not Started | Allow for custom mod assets |
| Not Started | Select world version to generate |
| Not Started | Add 26.2 assets |

See [ui.md](ui.md) for the current editor guide.

The Site tab today assumes **one** structure per stage (`offset_x` / `offset_z` on a single layer footprint). Nudge and placement are intentionally per-footprint so a later model can register many structures (each with its own offset and layer reference) without redoing the UX.

## Future plans

* Render preview system (embedded or side-by-side with editor)
* Structure preset browser
* Theme/style packs
* Advanced terrain generation
* Multi-biome support
* Animated build progression renders
