# renderers/top_view.py

from helpers.context import SchematicContext
from renderers.layer_panel import render_layer_blueprint


def render_floor_blueprints(ctx: SchematicContext):
    print("  ↳ Rendering floor blueprint panels...")

    for floor_name, layers in ctx.floor_map.items():
        if "roof" in floor_name.lower():
            continue

        render_layer_blueprint(ctx, floor_name, layers)