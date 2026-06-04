"""Block texture loading for the structure editor grid."""

from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QImage, QPixmap

from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.types import CellGrid, RawToken
from helpers.utils_schematics import resolve_cell_texture
from registries.loader import compile_texture_set

DEFAULT_ICON_SIZE = 48


def pil_to_qpixmap(image: Image.Image) -> QPixmap:
    rgba = image.convert("RGBA")
    qimage = QImage(
        rgba.tobytes("raw", "RGBA"),
        rgba.width,
        rgba.height,
        rgba.width * 4,
        QImage.Format.Format_RGBA8888,
    )
    return QPixmap.fromImage(qimage.copy())


class GridTextureCache:
    """Resolve schematic cell tokens to Qt icons using the render texture set."""

    def __init__(self, icon_size: int = DEFAULT_ICON_SIZE) -> None:
        self.icon_size = icon_size
        self._textures = compile_texture_set(
            "top",
            str(BLOCK_TEXTURES_FOLDER),
            icon_size,
        )
        self._icon_cache: dict[tuple[str, int, int], QIcon] = {}

    def icon_for_cell(
        self,
        raw_token: RawToken,
        *,
        layer_cells: CellGrid | None = None,
        row: int | None = None,
        col: int | None = None,
        size: int | None = None,
    ) -> QIcon | None:
        if raw_token == ".":
            return None

        cache_row = row if row is not None else -1
        cache_col = col if col is not None else -1
        render_size = size if size is not None else self.icon_size
        cache_key = (raw_token, cache_row, cache_col, render_size)

        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        image = resolve_cell_texture(
            raw_token,
            self._textures,
            view="top",
            size=render_size,
            layer_cells=layer_cells,
            cell_x=col,
            cell_z=row,
        )

        if image is None:
            return None

        icon = QIcon(pil_to_qpixmap(image))
        self._icon_cache[cache_key] = icon
        return icon

    def set_icon_size(self, icon_size: int) -> None:
        if icon_size == self.icon_size:
            return

        self.icon_size = icon_size
        self.clear_cache()

    def qt_icon_size(self) -> QSize:
        return QSize(self.icon_size, self.icon_size)

    def clear_cache(self) -> None:
        self._icon_cache.clear()

    def invalidate_cell(self, row: int, col: int) -> None:
        """Drop cached icons for a grid cell so token/variant changes repaint."""
        self._icon_cache = {
            key: icon for key, icon in self._icon_cache.items() if key[1] != row or key[2] != col
        }

    def invalidate_token(self, raw_token: str) -> None:
        """Drop cached icons for a token (all cells plus brush preview slot)."""
        self._icon_cache = {
            key: icon for key, icon in self._icon_cache.items() if key[0] != raw_token
        }
