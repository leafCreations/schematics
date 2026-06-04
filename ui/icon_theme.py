"""Load toolbar icons from ``assets/icons`` (bundled freedesktop theme)."""

from __future__ import annotations

import configparser

from PySide6.QtGui import QIcon

from helpers.paths import ASSETS_ROOT, UI_ICONS_FOLDER

_ICON_SIZES = (22, 24, 32)
_ACTION_CATEGORIES = ("actions", "devices")


def ui_icon_theme_name() -> str | None:
    """Return ``Name`` from ``assets/icons/index.theme``, if present."""
    theme_file = UI_ICONS_FOLDER / "index.theme"

    if not theme_file.is_file():
        return None

    parser = configparser.ConfigParser()
    parser.read(theme_file, encoding="utf-8")

    if parser.has_option("Icon Theme", "Name"):
        return parser.get("Icon Theme", "Name")

    return None


def configure_ui_icon_theme() -> None:
    """Prefer bundled ``assets/icons`` for :meth:`QIcon.fromTheme` lookups."""
    if not UI_ICONS_FOLDER.is_dir():
        return

    search_paths = [str(ASSETS_ROOT), *QIcon.themeSearchPaths()]
    QIcon.setThemeSearchPaths(search_paths)

    theme_name = ui_icon_theme_name()

    if theme_name:
        QIcon.setThemeName(theme_name)

    # Theme directory is ``icons/`` while Name may differ; also search that folder.
    icons_parent = str(UI_ICONS_FOLDER.parent)
    if icons_parent not in search_paths:
        QIcon.setThemeSearchPaths([icons_parent, *QIcon.themeSearchPaths()])


def icon_from_assets(name: str, *, prefer_symbolic: bool = True) -> QIcon:
    """Resolve a freedesktop icon name under ``assets/icons``."""
    if not UI_ICONS_FOLDER.is_dir():
        return QIcon()

    suffixes = ("-symbolic", "") if prefer_symbolic else ("", "-symbolic")

    for category in _ACTION_CATEGORIES:
        for size in _ICON_SIZES:
            for suffix in suffixes:
                path = UI_ICONS_FOLDER / category / str(size) / f"{name}{suffix}.svg"

                if path.is_file():
                    return QIcon(str(path))

    for suffix in suffixes:
        path = UI_ICONS_FOLDER / f"{name}{suffix}.svg"

        if path.is_file():
            return QIcon(str(path))

    return QIcon()
