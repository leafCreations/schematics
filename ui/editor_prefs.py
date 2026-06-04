"""Editor UI preferences (YAML application settings, not structure YAML)."""

from __future__ import annotations

from ui.app_settings import (
    EditorSettings,
    load_editor_settings,
    reset_editor_settings_cache,
    save_user_editor_settings,
)


def _settings() -> EditorSettings:
    return load_editor_settings()


def block_tooltips_enabled() -> bool:
    return _settings().block_tooltips


def set_block_tooltips_enabled(enabled: bool) -> None:
    settings = _settings()

    if settings.block_tooltips == enabled:
        return

    settings.block_tooltips = enabled
    save_user_editor_settings(settings)


def site_block_tooltips_enabled() -> bool:
    return block_tooltips_enabled()


def set_site_block_tooltips_enabled(enabled: bool) -> None:
    set_block_tooltips_enabled(enabled)


def grid_axis_labels_enabled() -> bool:
    return _settings().grid_axis_labels


def set_grid_axis_labels_enabled(enabled: bool) -> None:
    settings = _settings()

    if settings.grid_axis_labels == enabled:
        return

    settings.grid_axis_labels = enabled
    save_user_editor_settings(settings)


def panel_compass_visible() -> bool:
    return _settings().panel_compass


def set_panel_compass_visible(visible: bool) -> None:
    _set_panel("panel_compass", visible)


def panel_materials_visible() -> bool:
    return _settings().panel_materials


def set_panel_materials_visible(visible: bool) -> None:
    _set_panel("panel_materials", visible)


def panel_structure_settings_visible() -> bool:
    return _settings().panel_structure_settings


def set_panel_structure_settings_visible(visible: bool) -> None:
    _set_panel("panel_structure_settings", visible)


def _set_panel(field: str, visible: bool) -> None:
    settings = _settings()

    if getattr(settings, field) == visible:
        return

    setattr(settings, field, visible)
    save_user_editor_settings(settings)


def reset_editor_prefs_cache() -> None:
    """Clear cached settings (tests)."""
    reset_editor_settings_cache()
