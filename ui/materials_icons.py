"""Inventory-style icons for the live materials list."""

from __future__ import annotations

from PIL import Image, ImageDraw
from PySide6.QtGui import QIcon

from helpers.context import SchematicContext
from helpers.materials import draw_inventory_icon
from helpers.structure_tokens import ParsedToken, format_structure_token
from helpers.types import RawToken
from ui.texture_cache import pil_to_qpixmap


class MaterialsIconCache:
    def __init__(self, ctx: SchematicContext, *, icon_size: int = 24) -> None:
        self._ctx = ctx
        self._icon_size = icon_size
        self._cache: dict[tuple[str, str | None], QIcon] = {}

    def icon_for(
        self,
        display_name: str,
        texture_name: str | None,
        *,
        parsed: ParsedToken | None = None,
        raw_token: RawToken | None = None,
    ) -> QIcon:
        resolved_raw = raw_token or (format_structure_token(parsed) if parsed else None)
        cache_key = (display_name, texture_name, resolved_raw)

        if cache_key in self._cache:
            return self._cache[cache_key]

        size = self._icon_size
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw_inventory_icon(
            image,
            draw,
            self._ctx,
            texture_name,
            0,
            0,
            size=size,
            parsed=parsed,
            raw_token=raw_token,
        )
        icon = QIcon(pil_to_qpixmap(image))
        self._cache[cache_key] = icon
        return icon

    def clear(self) -> None:
        self._cache.clear()
