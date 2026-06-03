"""Editor UI preferences (not stored in structure YAML)."""

from __future__ import annotations

from PySide6.QtCore import QSettings

_SETTINGS = QSettings("structure_scripts", "editor")


_BLOCK_TOOLTIPS_KEY = "editor/block_tooltips"
_LEGACY_BLOCK_TOOLTIPS_KEY = "site/block_tooltips"


def _coerce_bool(value: object, default: bool) -> bool:
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}

    return bool(value)


def block_tooltips_enabled() -> bool:
    value = _SETTINGS.value(_BLOCK_TOOLTIPS_KEY)

    if value is None:
        value = _SETTINGS.value(_LEGACY_BLOCK_TOOLTIPS_KEY, True)

    return _coerce_bool(value, True)


def set_block_tooltips_enabled(enabled: bool) -> None:
    _SETTINGS.setValue(_BLOCK_TOOLTIPS_KEY, enabled)


def site_block_tooltips_enabled() -> bool:
    return block_tooltips_enabled()


def set_site_block_tooltips_enabled(enabled: bool) -> None:
    set_block_tooltips_enabled(enabled)
