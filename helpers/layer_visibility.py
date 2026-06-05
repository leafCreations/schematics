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
    """Site cross-section Y rows to draw: site ground plus non-empty overlay levels."""
    from helpers.landscape_utils import SITE_GROUND_Y, _site_layer_has_content

    layer_keys = [SITE_GROUND_Y]

    for site_y in sorted(key for key in site_map if key != SITE_GROUND_Y):
        if _site_layer_has_content(site_map[site_y], site_width, site_depth):
            layer_keys.append(site_y)

    return layer_keys
