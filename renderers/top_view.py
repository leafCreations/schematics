from helpers.context import SchematicContext
from helpers.layers import render_layer_group_blueprints


def render_floor_blueprints(ctx: SchematicContext):
    render_layer_group_blueprints(ctx, roofs=False)
