from collections import defaultdict

from helpers.context import SchematicContext
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
    if layer.get("name"):
        return str(layer["name"])

    if layer.get("group"):
        return str(layer["group"])

    if "index" in layer:
        return f"Layer {layer['index']}"

    return "Layer"


def render_layer_group_blueprints(ctx: SchematicContext, *, roofs: bool) -> None:
    label = "roof" if roofs else "floor"
    print(f"  ↳ Rendering {label} blueprint panels...")

    grouped_layers = defaultdict(list)

    for layer in ctx.layers:
        group_name = get_layer_group(layer)
        is_roof_group = "roof" in group_name.lower()

        if is_roof_group != roofs:
            continue

        grouped_layers[group_name].append(layer)

    for group_name, layers in grouped_layers.items():
        render_layer_blueprint(ctx, group_name, layers)
