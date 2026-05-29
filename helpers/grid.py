from helpers.context import SchematicContext


def get_structure_width(ctx: SchematicContext) -> int:
    return max(
        (len(row) for layer in ctx.layers for row in layer.get("cells", [])),
        default=1,
    )


def get_structure_depth(ctx: SchematicContext) -> int:
    return max(
        (len(layer.get("cells", [])) for layer in ctx.layers),
        default=1,
    )
