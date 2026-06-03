import helpers.constants as constants
from helpers.context import SchematicContext


def resolve_site_dimensions(grid: dict) -> tuple[int, int]:
    """Return (site_width, site_depth). Legacy ``site_size`` sets both to the same value."""
    if "site_width" in grid and "site_depth" in grid:
        return int(grid["site_width"]), int(grid["site_depth"])

    if "site_size" in grid:
        size = int(grid["site_size"])
        return size, size

    if "site_width" in grid:
        width = int(grid["site_width"])
        return width, int(grid.get("site_depth", width))

    if "site_depth" in grid:
        depth = int(grid["site_depth"])
        return int(grid.get("site_width", depth)), depth

    return 30, 30


def get_site_width(ctx: SchematicContext) -> int:
    return resolve_site_dimensions(ctx.grid)[0]


def get_site_depth(ctx: SchematicContext) -> int:
    return resolve_site_dimensions(ctx.grid)[1]


def get_site_size(ctx: SchematicContext) -> int:
    """Legacy helper: returns site width only.

    Prefer :func:`get_site_width` / :func:`get_site_depth`.
    """
    return get_site_width(ctx)


def get_offset_x(ctx: SchematicContext) -> int:
    return int(ctx.grid.get("offset_x", 0))


def get_offset_z(ctx: SchematicContext) -> int:
    return int(ctx.grid.get("offset_z", 0))


def get_path_center_local_x(ctx: SchematicContext) -> int:
    """Local X (within structure footprint) used to center auto-generated paths.

    Reads ``path_center_local_x`` from grid metadata. ``stair_local_x`` is accepted
    as a deprecated alias. When neither is set, defaults to the horizontal center
    of the structure footprint (not tied to STAIRS blocks in layers).
    """
    grid = ctx.grid

    if "path_center_local_x" in grid:
        return int(grid["path_center_local_x"])

    if "stair_local_x" in grid:
        return int(grid["stair_local_x"])

    structure_width = get_structure_width(ctx)
    return max(0, structure_width // 2)


def get_stair_local_x(ctx: SchematicContext) -> int:
    """Deprecated alias for :func:`get_path_center_local_x`."""
    return get_path_center_local_x(ctx)


def get_site_structure_layer_indices(ctx: SchematicContext) -> list[int]:
    configured = ctx.grid.get("site_structure_layers")

    if configured is not None:
        return [int(index) for index in configured]

    return constants.DEFAULT_SITE_STRUCTURE_LAYERS[: len(ctx.layers)]


def get_worldgen_base_y(ctx: SchematicContext) -> int:
    return int(ctx.grid.get("worldgen_base_y", constants.DEFAULT_WORLDGEN_BASE_Y))


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
