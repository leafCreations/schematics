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
    ) -> QIcon | None:
        if raw_token == ".":
            return None

        cache_key = (raw_token, row if row is not None else -1, col if col is not None else -1)

        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        image = resolve_cell_texture(
            raw_token,
            self._textures,
            view="top",
            size=self.icon_size,
            layer_cells=layer_cells,
            cell_x=col,
            cell_z=row,
        )

        if image is None:
            return None

        icon = QIcon(pil_to_qpixmap(image))
        self._icon_cache[cache_key] = icon
        return icon

    def qt_icon_size(self) -> QSize:
        return QSize(self.icon_size, self.icon_size)

    def clear_cache(self) -> None:
        self._icon_cache.clear()
