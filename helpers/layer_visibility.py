"""Per-layer visibility for render output (editor keeps all layers in the stack)."""

from __future__ import annotations

from typing import Any

from helpers.types import SiteMap


def is_layer_visible(layer: dict[str, Any]) -> bool:
    """Return whether *layer* contributes to renders (default visible)."""
    return layer.get("visible", True) is not False


def set_layer_visible(layer: dict[str, Any], visible: bool) -> None:
    """Set visibility on *layer*; omit ``visible`` when shown."""
    if visible:
        layer.pop("visible", None)
    else:
        layer["visible"] = False


def visible_layer_array_indices(
    layers: list[dict[str, Any]],
    grid: dict[str, Any] | None = None,
) -> list[int]:
    """List positions in *layers* that contribute to renders (facades, worldgen, etc.)."""
    from helpers.layer_groups import visible_layer_array_indices as _visible_with_groups

    return _visible_with_groups(layers, grid)


def site_facade_layer_keys(site_map: SiteMap, *, site_width: int, site_depth: int) -> list[int]:
    """Site cross-section Y rows to draw: ground (-1) plus non-empty overlay levels."""
    layer_keys = [-1]

    for site_y in (0, 1):
        for z in range(site_depth):
            row = site_map[site_y][z]

            for x in range(min(site_width, len(row))):
                if row[x] != ".":
                    layer_keys.append(site_y)
                    break
            else:
                continue

            break

    return layer_keys
