from helpers.context import SchematicContext
from helpers.layers import render_layer_group_blueprints


def render_roof_blueprints(ctx: SchematicContext):
    render_layer_group_blueprints(ctx, roofs=True)
