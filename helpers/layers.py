from collections import defaultdict

from helpers.context import SchematicContext
from helpers.layer_groups import is_layer_render_visible
from helpers.layer_management import layer_worldgen_index
from renderers.layer_panel import render_layer_blueprint


def get_layer_group(layer: dict) -> str:
    if layer.get("group"):
        return str(layer["group"])

    if layer.get("floor"):
        return str(layer["floor"])

    layer_name = str(layer.get("name", "Floor"))

    if ":" in layer_name:
        return layer_name.split(":", 1)[0].strip()

    if " - " in layer_name:
        return layer_name.split(" - ", 1)[0].strip()

    if "roof" in layer_name.lower():
        return "Roof"

    return "Floor"


def get_layer_display_name(layer: dict) -> str:
    description = layer.get("description")

    if isinstance(description, str) and description.strip():
        base = description.strip()
    elif layer.get("name"):
        base = str(layer["name"])
    elif layer.get("group"):
        base = str(layer["group"])
    elif "index" in layer:
        base = f"Layer {layer['index']}"
    else:
        base = "Layer"

    if "index" in layer:
        return f"{base} (Y={int(layer['index'])})"

    return base


def render_layer_group_blueprints(ctx: SchematicContext, *, roofs: bool) -> None:
    label = "roof" if roofs else "floor"
    print(f"  ↳ Rendering {label} blueprint panels...")

    grouped_layers: dict[str, list[tuple[int, dict]]] = defaultdict(list)

    for layer_array_index, layer in enumerate(ctx.layers):
        if not is_layer_render_visible(layer, layer_array_index, ctx.grid):
            continue

        group_name = get_layer_group(layer)
        is_roof_group = "roof" in group_name.lower()

        if is_roof_group != roofs:
            continue

        grouped_layers[group_name].append((layer_array_index, layer))

    for group_name, layer_entries in grouped_layers.items():
        layer_entries.sort(
            key=lambda entry: (
                layer_worldgen_index(entry[1], entry[0]),
                entry[0],
            )
        )
        layers = [layer for _index, layer in layer_entries]
        render_layer_blueprint(ctx, group_name, layers)
