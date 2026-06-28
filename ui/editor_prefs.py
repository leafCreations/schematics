"""Editor UI preferences (YAML application settings, not structure YAML)."""

from __future__ import annotations

from ui.app_settings import (
    EditorSettings,
    OrbitCameraPose,
    clamp_orbit_camera_move_speed,
    clamp_preview_zoom_percent,
    load_editor_settings,
    orbit_camera_pose_storage_key,
    parse_orbit_camera_hud_placement,
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


def preview_zoom_percent() -> int:
    return _settings().preview_zoom_percent


def set_preview_zoom_percent(percent: int) -> None:
    settings = _settings()
    clamped = clamp_preview_zoom_percent(percent)

    if settings.preview_zoom_percent == clamped:
        return

    settings.preview_zoom_percent = clamped
    save_user_editor_settings(settings)


def orbit_camera_pose(structure: str, stage: int) -> OrbitCameraPose | None:
    key = orbit_camera_pose_storage_key(structure, stage)
    return _settings().orbit_camera_poses.get(key)


def set_orbit_camera_pose(structure: str, stage: int, pose: OrbitCameraPose) -> None:
    key = orbit_camera_pose_storage_key(structure, stage)
    settings = _settings()
    if settings.orbit_camera_poses.get(key) == pose:
        return
    settings.orbit_camera_poses[key] = pose
    save_user_editor_settings(settings)


def orbit_camera_hud_visible() -> bool:
    return _settings().orbit_camera_hud_visible


def set_orbit_camera_hud_visible(visible: bool) -> None:
    settings = _settings()
    if settings.orbit_camera_hud_visible == visible:
        return
    settings.orbit_camera_hud_visible = visible
    save_user_editor_settings(settings)


def orbit_camera_move_speed() -> float:
    return _settings().orbit_camera_move_speed


def set_orbit_camera_move_speed(speed: float) -> None:
    settings = _settings()
    clamped = clamp_orbit_camera_move_speed(speed)
    if settings.orbit_camera_move_speed == clamped:
        return
    settings.orbit_camera_move_speed = clamped
    save_user_editor_settings(settings)


def orbit_camera_hud_placement() -> str:
    return _settings().orbit_camera_hud_placement


def set_orbit_camera_hud_placement(placement: str) -> None:
    settings = _settings()
    parsed = parse_orbit_camera_hud_placement(placement)
    if settings.orbit_camera_hud_placement == parsed:
        return
    settings.orbit_camera_hud_placement = parsed
    save_user_editor_settings(settings)


def orbit_camera_hud_crosshair_visible() -> bool:
    return _settings().orbit_camera_hud_crosshair_visible


def set_orbit_camera_hud_crosshair_visible(visible: bool) -> None:
    settings = _settings()
    if settings.orbit_camera_hud_crosshair_visible == visible:
        return
    settings.orbit_camera_hud_crosshair_visible = visible
    save_user_editor_settings(settings)


def _set_panel(field: str, visible: bool) -> None:
    settings = _settings()

    if getattr(settings, field) == visible:
        return

    setattr(settings, field, visible)
    save_user_editor_settings(settings)


def reset_editor_prefs_cache() -> None:
    """Clear cached settings (tests)."""
    reset_editor_settings_cache()
