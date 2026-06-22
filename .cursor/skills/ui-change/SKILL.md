---
name: ui-change
description: >-
  Checklist for structure_scripts editor UI changes under ui/. Use when adding or
  modifying panels, dialogs, grid toolbar, properties brush, site tab, palette,
  main_window wiring, or user-facing editor behavior documented in docs/ui.md.
---

# UI Change

Checklist for PySide6 editor work. Minimize churn: follow existing patterns; wire in `main_window.py`; test narrowly.

Start with [agent-triage](../agent-triage/SKILL.md) and [repo-map](../repo-map/SKILL.md).

## Before editing

| Touching | Read |
| -------- | ---- |
| New/refactored panel | `.cursor/rules/ui-panels.mdc` |
| Modal dialog / prompt | `.cursor/rules/ui-dialogs.mdc` |
| Selector/Eraser split toolbar | `.cursor/rules/ui-split-buttons.mdc` |
| New preference / tooltip | `.cursor/rules/ui-properties.mdc` |
| User-facing behavior | `docs/ui.md`, `docs/editor-properties.md` |

**Do not** read all rules for a one-line label fix.

## Panel checklist

1. Subclass `QGroupBox` — **no** title in `super().__init__()`.
2. Title row via `ui/widgets/panel_header.py`:
   - `create_simple_titled_panel_layout` — title only
   - `create_titled_panel_layout` — title + header buttons
   - `create_nested_group_layout` — nested sections (properties panel)
3. Header icons: 18px — `panel_icon_size()`, `make_panel_tool_button()`.
4. Panel emits signals (`*_requested`); **wire in `ui/main_window.py` only**.
5. Hiding panels: update `_update_palette_column_layout()` or `_update_structure_tools_column_layout()` so columns don’t leave gaps.

## Dialog checklist

1. Subclass `QDialog` in `ui/widgets/`.
2. Use `ui/dialog_layout.py`: `create_dialog_shell`, `apply_dialog_field_style` (32px), `create_dialog_button_box`.
3. **No** `QInputDialog` for new prompts — use `InputTextDialog`.
4. Hint: **"Changes are saved when you click OK."**
5. On accept: `main_window._persist_dialog_changes(...)` — don’t only set dirty flags.

## Grid toolbar

- Tools live in `ui/widgets/layer_tools_panel.py` / `LayerActionToolbar`.
- Toolbar icons: 22px — `toolbar_icon_size()`.
- Split buttons: menu pops from **container** bottom-left (see ui-split-buttons.mdc).

## Persistence — what saves where

| UI surface | Saves to |
| ---------- | -------- |
| Structure grid cells | `layers/layer_NN.yaml` — Save Layer |
| Site settings, paths, groups order | Manifest `structure.yaml` + `stage.yaml` — Save Site Settings |
| Layer dialog OK | Auto-save via `_persist_dialog_changes` |
| View prefs (tooltips, axis labels) | `~/.config/structure_scripts/editor_settings.yaml` |

Details: `docs/structure-tokens.md`, `docs/editor-properties.md`.

## main_window.py

- **Orchestration only** — grep for similar handler before reading whole file.
- New panel: `addWidget` + layout updater + View menu if dismissible.
- Tool sync: `_sync_layer_tool_panels()` pattern for paint/selector/eraser visibility.

## Tests

Use [targeted-testing](../targeted-testing/SKILL.md) — **not** full suite.

| Changed | Run |
| ------- | --- |
| `ui/widgets/palette_panel.py` | `tests/test_palette_panel.py` |
| `ui/widgets/grid.py` | `tests/test_grid_scrollbars.py` + related |
| `ui/widgets/properties_panel.py` | `tests/test_properties_panel.py` |
| `ui/document.py` | `tests/test_ui_document.py` |
| `ui/main_window.py` | `tests/test_main_window.py` |
| Dialog widget | dialog tests if present + main_window if wired |

Qt tests may need full shell permissions (segfault in sandbox).

## Manual verify

After non-trivial UI changes:

```bash
bash scripts/run-ui residence 1
```

Use **View → Reload Window** (`Ctrl+Shift+Q`) after code edits instead of full restart when possible. See [run-ui](../run-ui/SKILL.md).

## Docs

Update when user-facing:

- `docs/ui.md` — developer reference
- `docs/structure-editor-guide.md` — user workflow
- `docs/editor-properties.md` — new fields / save targets

Skip doc sweep for internal refactors with no behavior change.

## Do not

- `QGroupBox("Title")` for panel names
- Per-menu stylesheets — use `configure_ui_menus()` / global menu style
- Business logic heavy in widgets — delegate to helpers
- Full pytest after every widget tweak
- Launch UI for docs-only commits

## End checklist

```
- [ ] panel_header / dialog_layout patterns used
- [ ] Signals wired in main_window.py
- [ ] Column layout updated if panel show/hide changed
- [ ] _persist_dialog_changes on dialog OK
- [ ] Targeted UI tests run
- [ ] docs/ui.md updated if user-visible
```

Panel refactor backlog: `docs/ui-panel-refactor.md`.
