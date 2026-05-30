from helpers.context import SchematicContext


def get_site_size(ctx: SchematicContext) -> int:
    return int(ctx.grid.get("site_size", 30))


def get_offset_x(ctx: SchematicContext) -> int:
    return int(ctx.grid.get("offset_x", 0))


def get_offset_z(ctx: SchematicContext) -> int:
    return int(ctx.grid.get("offset_z", 0))


def get_structure_width(ctx: SchematicContext) -> int:
    return max(
        (len(row) for layer in ctx.layers for row in layer.get("cells", [])),
        default=1,
    )


def get_structure_height(ctx: SchematicContext) -> int:
    return max(len(ctx.layers), 1)


def get_structure_depth(ctx: SchematicContext) -> int:
    return max(
        (len(layer.get("cells", [])) for layer in ctx.layers),
        default=1,
    )


def is_inside_structure(ctx: SchematicContext, local_x: int, local_z: int) -> bool:
    return 0 <= local_x < get_structure_width(ctx) and 0 <= local_z < get_structure_depth(ctx)
