# Roadmap

## Design goals

* Registry-driven customization
* Modular renderer expansion
* Additional structure presets
* Advanced landscaping systems
* Desktop UI for structure authoring

## UI (in progress)

| Status | Item |
| ------ | ---- |
| Done | PySide6 editor shell, palette tabs, texture grid |
| Done | Paint / erase, per-layer save, unsaved indicators |
| Done | `helpers/block_picker.py`, palette integrity validation |
| Done | Generate renders from editor (Render tab) |
| Planned | Live render preview pane |
| Planned | In-app structure metadata editing |
| Done | Undo/redo (paint/erase, structure resize, site grid, placement nudge) |
| Done | Site path brush (trim / randomized path / trim, configurable width) |
| Planned | Fill, clipboard |
| Planned | Multiple structures per site — each selectable and nudged independently on the Site tab |

See [ui.md](ui.md) for the current editor guide.

The Site tab today assumes **one** structure per stage (`offset_x` / `offset_z` on a single layer footprint). Nudge and placement are intentionally per-footprint so a later model can register many structures (each with its own offset and layer reference) without redoing the UX.

## Future plans

* Render preview system (embedded or side-by-side with editor)
* Structure preset browser
* Theme/style packs
* Advanced terrain generation
* Multi-biome support
* Animated build progression renders
