from helpers import grid as grid_utils
from helpers.context import SchematicContext
from helpers.layer_groups import is_layer_render_visible
from helpers.types import CellGrid, RawToken


def get_cell(
    cells: CellGrid,
    x: int,
    z: int,
    *,
    empty: str | None = ".",
) -> str | None:
    """Return ``cells[z][x]``, or *empty* when out of bounds.

    Pass ``empty=None`` when a missing neighbor should be distinguished from air
    (e.g. fence adjacency in worldgen).
    """
    if z < 0 or z >= len(cells):
        return empty

    row = cells[z]

    if x < 0 or x >= len(row):
        return empty

    return row[x]


def get_structure_cell(
    ctx: SchematicContext,
    layer_array_index: int,
    x: int,
    z: int,
    *,
    empty: RawToken = ".",
) -> RawToken:
    """Return the raw token at local structure coordinates ``(x, z)``.

    ``layer_array_index`` is the position in ``ctx.layers`` (0 = first layer file),
    **not** the layer file's worldgen ``index`` field.
    """
    if layer_array_index < 0 or layer_array_index >= len(ctx.layers):
        return empty

    layer = ctx.layers[layer_array_index]

    if not is_layer_render_visible(layer, layer_array_index, ctx.grid):
        return empty

    cells = layer.get("cells", [])
    result = get_cell(cells, x, z, empty=empty)

    return empty if result is None else result


def get_structure_cell_at_site(
    ctx: SchematicContext,
    layer_array_index: int,
    global_x: int,
    global_z: int,
    *,
    empty: RawToken = ".",
) -> RawToken:
    """Return the raw token at site coordinates, mapped into the structure grid.

    See :func:`get_structure_cell` for ``layer_array_index`` semantics.
    """
    local_x = global_x - grid_utils.get_offset_x(ctx)
    local_z = global_z - grid_utils.get_offset_z(ctx)

    if not grid_utils.is_inside_structure(ctx, local_x, local_z):
        return empty

    return get_structure_cell(ctx, layer_array_index, local_x, local_z, empty=empty)
