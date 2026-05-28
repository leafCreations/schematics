from collections import defaultdict

from helpers.context import SchematicContext
from renderers.layer_panel import render_layer_blueprint
from renderers.top_view import _get_layer_group


def render_roof_blueprints(ctx: SchematicContext):
    print("  ↳ Rendering roof blueprint panels...")

    grouped_layers = defaultdict(list)

    for layer in ctx.layers:
        group_name = _get_layer_group(layer)

        if "roof" not in group_name.lower():
            continue

        grouped_layers[group_name].append(layer)

    for group_name, layers in grouped_layers.items():
        render_layer_blueprint(ctx, group_name, layers)
