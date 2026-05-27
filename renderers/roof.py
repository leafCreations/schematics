# renderers/roof.py

from helpers.context import SchematicContext
from renderers.layer_panel import render_layer_blueprint


def render_roof_blueprints(ctx: SchematicContext):
    print("  ↳ Rendering roof blueprint panels...")

    for floor_name, layers in ctx.floor_map.items():
        if "roof" not in floor_name.lower():
            continue

        render_layer_blueprint(ctx, floor_name, layers)