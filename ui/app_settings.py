"""Load and save Structure Editor application settings (YAML)."""

from __future__ import annotations

import math
import os
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from helpers.paths import BASE_DIR

_BUNDLED_PATH = BASE_DIR / "config" / "editor_settings.yaml"
_USER_DIR_NAME = "structure_scripts"
_USER_FILE_NAME = "editor_settings.yaml"
_ENV_OVERRIDE = "STRUCTURE_SCRIPTS_EDITOR_SETTINGS"

_LEGACY_QSETTINGS_ORG = "structure_scripts"
_LEGACY_QSETTINGS_APP = "editor"
_LEGACY_BLOCK_TOOLTIPS_KEY = "editor/block_tooltips"
_LEGACY_SITE_BLOCK_TOOLTIPS_KEY = "site/block_tooltips"
_LEGACY_GRID_AXIS_LABELS_KEY = "editor/grid_axis_labels"

_PREVIEW_ZOOM_MIN = 25
_PREVIEW_ZOOM_MAX = 400
_DEFAULT_PREVIEW_ZOOM_PERCENT = 100

_ORBIT_CAMERA_MOVE_SPEED_MIN = 0.2
_ORBIT_CAMERA_MOVE_SPEED_MAX = 1.0
_DEFAULT_ORBIT_CAMERA_MOVE_SPEED = 0.65
ORBIT_CAMERA_MOVE_SPEED_WHEEL_STEP = 0.05

_DEFAULT_ORBIT_CAMERA_HUD_PLACEMENT = "top_right"
_ORBIT_CAMERA_HUD_PLACEMENTS = frozenset(
    {
        "top_left",
        "top_center",
        "top_right",
        "middle_left",
        "middle_right",
        "bottom_left",
        "bottom_center",
        "bottom_right",
    },
)

_ORBIT_ELEVATION_MIN = -1.4
_ORBIT_ELEVATION_MAX = 1.4

_cached: EditorSettings | None = None


@dataclass(frozen=True)
class OrbitCameraPose:
    position: tuple[float, float, float]
    azimuth: float
    elevation: float


def parse_orbit_camera_position(value: object) -> tuple[float, float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return None
    try:
        coords = tuple(float(item) for item in value)
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(item) for item in coords):
        return None
    return coords


def parse_orbit_camera_azimuth(value: object) -> float | None:
    try:
        azimuth = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(azimuth):
        return None
    return azimuth


def parse_orbit_camera_elevation(value: object) -> float | None:
    try:
        elevation = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(elevation):
        return None
    if elevation < _ORBIT_ELEVATION_MIN or elevation > _ORBIT_ELEVATION_MAX:
        return None
    return elevation


def orbit_camera_pose_storage_key(structure: str, stage: int) -> str:
    normalized = str(structure).strip().lower()
    return f"{normalized}/{int(stage)}"


def _parse_orbit_camera_pose_entry(entry: object) -> OrbitCameraPose | None:
    if not isinstance(entry, dict):
        return None
    position = parse_orbit_camera_position(entry.get("position"))
    azimuth = parse_orbit_camera_azimuth(entry.get("azimuth"))
    elevation = parse_orbit_camera_elevation(entry.get("elevation"))
    if position is None or azimuth is None or elevation is None:
        return None
    return OrbitCameraPose(position=position, azimuth=azimuth, elevation=elevation)


def orbit_camera_poses_from_mapping(viewer: dict[str, Any]) -> dict[str, OrbitCameraPose]:
    raw = viewer.get("orbit_camera_poses")
    if not isinstance(raw, dict):
        return {}

    poses: dict[str, OrbitCameraPose] = {}
    for key, entry in raw.items():
        storage_key = str(key).strip().lower()
        if not storage_key:
            continue
        pose = _parse_orbit_camera_pose_entry(entry)
        if pose is not None:
            poses[storage_key] = pose
    return poses


def clamp_preview_zoom_percent(percent: object) -> int:
    try:
        value = int(percent)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return _DEFAULT_PREVIEW_ZOOM_PERCENT
    return max(_PREVIEW_ZOOM_MIN, min(_PREVIEW_ZOOM_MAX, value))


def parse_orbit_camera_hud_placement(value: object) -> str:
    if isinstance(value, str):
        key = value.strip().lower()
        if key in _ORBIT_CAMERA_HUD_PLACEMENTS:
            return key
    return _DEFAULT_ORBIT_CAMERA_HUD_PLACEMENT


def clamp_orbit_camera_move_speed(value: object) -> float:
    try:
        speed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return _DEFAULT_ORBIT_CAMERA_MOVE_SPEED
    if not math.isfinite(speed):
        return _DEFAULT_ORBIT_CAMERA_MOVE_SPEED
    return max(
        _ORBIT_CAMERA_MOVE_SPEED_MIN,
        min(_ORBIT_CAMERA_MOVE_SPEED_MAX, speed),
    )


@dataclass
class EditorSettings:
    block_tooltips: bool = True
    grid_axis_labels: bool = True
    panel_compass: bool = True
    panel_materials: bool = True
    panel_structure_settings: bool = True
    preview_zoom_percent: int = _DEFAULT_PREVIEW_ZOOM_PERCENT
    orbit_camera_poses: dict[str, OrbitCameraPose] = field(default_factory=dict)
    orbit_camera_hud_visible: bool = True
    orbit_camera_hud_placement: str = _DEFAULT_ORBIT_CAMERA_HUD_PLACEMENT
    orbit_camera_hud_crosshair_visible: bool = True
    orbit_camera_move_speed: float = _DEFAULT_ORBIT_CAMERA_MOVE_SPEED
    recent_structures: list[tuple[str, int]] = field(default_factory=list)


def bundled_settings_path() -> Path:
    return _BUNDLED_PATH


def user_settings_path() -> Path:
    override = os.environ.get(_ENV_OVERRIDE)

    if override:
        return Path(override).expanduser()

    config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(config_home) if config_home else Path.home() / ".config"

    return base / _USER_DIR_NAME / _USER_FILE_NAME


def _coerce_bool(value: object, default: bool) -> bool:
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}

    return bool(value)


def _settings_from_mapping(data: dict[str, Any]) -> EditorSettings:
    display = data.get("display") if isinstance(data.get("display"), dict) else {}
    panels = data.get("panels") if isinstance(data.get("panels"), dict) else {}
    viewer = data.get("viewer") if isinstance(data.get("viewer"), dict) else {}
    recent = data.get("recent") if isinstance(data.get("recent"), dict) else {}
    opened = recent.get("opened") if isinstance(recent.get("opened"), list) else []

    parsed_recent: list[tuple[str, int]] = []

    for item in opened:
        if not isinstance(item, dict):
            continue

        structure = str(item.get("structure", "")).strip().lower()

        if not structure:
            continue

        try:
            stage = int(item.get("stage", 1))
        except (TypeError, ValueError):
            continue

        if stage < 1:
            continue

        parsed_recent.append((structure, stage))

    return EditorSettings(
        block_tooltips=_coerce_bool(display.get("block_tooltips"), True),
        grid_axis_labels=_coerce_bool(display.get("grid_axis_labels"), True),
        panel_compass=_coerce_bool(panels.get("compass"), True),
        panel_materials=_coerce_bool(panels.get("materials"), True),
        panel_structure_settings=_coerce_bool(panels.get("structure_settings"), True),
        preview_zoom_percent=clamp_preview_zoom_percent(
            viewer.get("preview_zoom_percent", _DEFAULT_PREVIEW_ZOOM_PERCENT)
        ),
        orbit_camera_poses=orbit_camera_poses_from_mapping(viewer),
        orbit_camera_hud_visible=_coerce_bool(viewer.get("orbit_camera_hud"), True),
        orbit_camera_hud_placement=parse_orbit_camera_hud_placement(
            viewer.get("orbit_camera_hud_placement", _DEFAULT_ORBIT_CAMERA_HUD_PLACEMENT),
        ),
        orbit_camera_hud_crosshair_visible=_coerce_bool(
            viewer.get("orbit_camera_hud_crosshair"),
            True,
        ),
        orbit_camera_move_speed=clamp_orbit_camera_move_speed(
            viewer.get("orbit_camera_move_speed", _DEFAULT_ORBIT_CAMERA_MOVE_SPEED),
        ),
        recent_structures=parsed_recent,
    )


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    if raw is None:
        return {}

    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a YAML mapping at the top level")

    return raw


def _viewer_settings_mapping(settings: EditorSettings) -> dict[str, Any]:
    viewer: dict[str, Any] = {
        "preview_zoom_percent": settings.preview_zoom_percent,
        "orbit_camera_hud": settings.orbit_camera_hud_visible,
        "orbit_camera_hud_placement": settings.orbit_camera_hud_placement,
        "orbit_camera_hud_crosshair": settings.orbit_camera_hud_crosshair_visible,
        "orbit_camera_move_speed": settings.orbit_camera_move_speed,
    }
    if settings.orbit_camera_poses:
        viewer["orbit_camera_poses"] = {
            key: {
                "azimuth": pose.azimuth,
                "elevation": pose.elevation,
                "position": list(pose.position),
            }
            for key, pose in settings.orbit_camera_poses.items()
        }
    return viewer


def settings_to_mapping(settings: EditorSettings) -> dict[str, Any]:
    return {
        "display": {
            "block_tooltips": settings.block_tooltips,
            "grid_axis_labels": settings.grid_axis_labels,
        },
        "panels": {
            "compass": settings.panel_compass,
            "materials": settings.panel_materials,
            "structure_settings": settings.panel_structure_settings,
        },
        "viewer": _viewer_settings_mapping(settings),
        "recent": {
            "opened": [
                {"structure": structure, "stage": stage}
                for structure, stage in settings.recent_structures
            ]
        },
    }


def merge_settings(base: EditorSettings, override: EditorSettings) -> EditorSettings:
    merged = deepcopy(base)
    data = settings_to_mapping(merged)
    overlay = settings_to_mapping(override)

    for section, values in overlay.items():
        if isinstance(values, dict):
            data.setdefault(section, {}).update(values)

    return _settings_from_mapping(data)


def _migrate_legacy_qsettings() -> EditorSettings | None:
    try:
        from PySide6.QtCore import QSettings
    except ImportError:
        return None

    store = QSettings(_LEGACY_QSETTINGS_ORG, _LEGACY_QSETTINGS_APP)
    block_value = store.value(_LEGACY_BLOCK_TOOLTIPS_KEY)

    if block_value is None:
        block_value = store.value(_LEGACY_SITE_BLOCK_TOOLTIPS_KEY)

    axis_value = store.value(_LEGACY_GRID_AXIS_LABELS_KEY)

    if block_value is None and axis_value is None:
        return None

    return EditorSettings(
        block_tooltips=_coerce_bool(block_value, True),
        grid_axis_labels=_coerce_bool(axis_value, True),
    )


def load_editor_settings(*, force_reload: bool = False) -> EditorSettings:
    global _cached

    if _cached is not None and not force_reload:
        return _cached

    bundled = _settings_from_mapping(_load_yaml_mapping(bundled_settings_path()))
    user_path = user_settings_path()

    if user_path.is_file():
        settings = merge_settings(bundled, _settings_from_mapping(_load_yaml_mapping(user_path)))
    else:
        settings = bundled
        legacy = _migrate_legacy_qsettings()

        if legacy is not None:
            settings = merge_settings(settings, legacy)

        save_user_editor_settings(settings)

    _cached = settings
    return settings


def save_user_editor_settings(settings: EditorSettings) -> None:
    global _cached

    path = user_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            settings_to_mapping(settings),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    _cached = settings


def reset_editor_settings_cache() -> None:
    global _cached
    _cached = None


def sync_editor_settings_from_ui(
    *,
    block_tooltips: bool,
    grid_axis_labels: bool,
    panel_compass: bool,
    panel_materials: bool,
    panel_structure_settings: bool,
    preview_zoom_percent: int | None = None,
) -> None:
    """Write the current UI state to the user settings file."""
    current = load_editor_settings()
    zoom = (
        clamp_preview_zoom_percent(preview_zoom_percent)
        if preview_zoom_percent is not None
        else current.preview_zoom_percent
    )
    settings = EditorSettings(
        block_tooltips=block_tooltips,
        grid_axis_labels=grid_axis_labels,
        panel_compass=panel_compass,
        panel_materials=panel_materials,
        panel_structure_settings=panel_structure_settings,
        preview_zoom_percent=zoom,
        orbit_camera_poses=dict(current.orbit_camera_poses),
        orbit_camera_hud_visible=current.orbit_camera_hud_visible,
        orbit_camera_hud_placement=current.orbit_camera_hud_placement,
        orbit_camera_hud_crosshair_visible=current.orbit_camera_hud_crosshair_visible,
        orbit_camera_move_speed=current.orbit_camera_move_speed,
        recent_structures=list(current.recent_structures),
    )
    save_user_editor_settings(settings)


def load_recent_structures() -> list[tuple[str, int]]:
    return list(load_editor_settings().recent_structures)


def save_recent_structures(entries: list[tuple[str, int]]) -> None:
    current = load_editor_settings()
    current.recent_structures = list(entries)
    save_user_editor_settings(current)


def add_recent_structure(structure: str, stage: int, *, limit: int = 10) -> None:
    normalized = str(structure).strip().lower()

    if not normalized:
        return

    stage_value = int(stage)

    if stage_value < 1:
        return

    current = load_editor_settings()
    existing = [
        (item_structure, item_stage)
        for item_structure, item_stage in current.recent_structures
        if not (item_structure == normalized and item_stage == stage_value)
    ]
    existing.insert(0, (normalized, stage_value))
    current.recent_structures = existing[: max(1, int(limit))]
    save_user_editor_settings(current)


def clear_recent_structures() -> None:
    current = load_editor_settings()
    current.recent_structures = []
    save_user_editor_settings(current)
