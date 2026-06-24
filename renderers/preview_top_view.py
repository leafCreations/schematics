"""Per-layer top-down blueprints for in-app preview (preview session dir only)."""

from __future__ import annotations

from helpers.context import SchematicContext
from helpers.layer_groups import is_layer_render_visible, layer_label
from helpers.layer_management import layer_worldgen_index
from renderers.layer_panel import render_single_layer_preview_blueprint


def render_preview_group_blueprints(ctx: SchematicContext, group_name: str) -> None:
    """Render one PNG per visible layer in the group, sorted by ascending Y index."""
    if "roof" in group_name.lower():
        return

    layer_entries: list[tuple[int, dict]] = []

    for list_index, layer in enumerate(ctx.layers):
        if not is_layer_render_visible(layer, list_index, ctx.grid):
            continue

        if layer_label(layer, list_index) != group_name:
            continue

        layer_entries.append((list_index, layer))

    layer_entries.sort(
        key=lambda entry: (layer_worldgen_index(entry[1], entry[0]), entry[0]),
    )

    for list_index, layer in layer_entries:
        render_single_layer_preview_blueprint(ctx, group_name, layer, list_index)
