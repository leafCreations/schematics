"""Load and save Structure Editor application settings (YAML)."""

from __future__ import annotations

import os
from copy import deepcopy
from dataclasses import dataclass
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

_cached: EditorSettings | None = None


@dataclass
class EditorSettings:
    block_tooltips: bool = True
    grid_axis_labels: bool = True
    panel_compass: bool = True
    panel_materials: bool = True
    panel_structure_settings: bool = True


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

    return EditorSettings(
        block_tooltips=_coerce_bool(display.get("block_tooltips"), True),
        grid_axis_labels=_coerce_bool(display.get("grid_axis_labels"), True),
        panel_compass=_coerce_bool(panels.get("compass"), True),
        panel_materials=_coerce_bool(panels.get("materials"), True),
        panel_structure_settings=_coerce_bool(panels.get("structure_settings"), True),
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
) -> None:
    """Write the current UI state to the user settings file."""
    settings = EditorSettings(
        block_tooltips=block_tooltips,
        grid_axis_labels=grid_axis_labels,
        panel_compass=panel_compass,
        panel_materials=panel_materials,
        panel_structure_settings=panel_structure_settings,
    )
    save_user_editor_settings(settings)
