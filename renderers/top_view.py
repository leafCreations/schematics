from collections import defaultdict

from helpers.context import SchematicContext
from renderers.layer_panel import render_layer_blueprint


def _get_layer_group(layer: dict) -> str:
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


def render_floor_blueprints(ctx: SchematicContext):
    print("  ↳ Rendering floor blueprint panels...")

    grouped_layers = defaultdict(list)

    for layer in ctx.layers:
        group_name = _get_layer_group(layer)

        if "roof" in group_name.lower():
            continue

        grouped_layers[group_name].append(layer)

    for group_name, layers in grouped_layers.items():
        render_layer_blueprint(ctx, group_name, layers)
