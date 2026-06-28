"""Axis-aligned mesh builders for the 3D orbit preview."""

from __future__ import annotations

from dataclasses import dataclass

from helpers.context import SchematicContext
from helpers.grid import get_offset_x, get_offset_z
from helpers.layer_groups import is_layer_render_visible
from helpers.layer_management import layer_worldgen_index

# Outset exterior quads so perpendicular faces overlap at block edges (T-junction cracks).
ORBIT_FACE_OVERLAP = 0.005

# Unit-cube face quads at block origin (x, y, z) → (x+1, y+1, z+1).
# Each entry: normal, then four corner offsets from block min corner.
_CUBE_FACES: tuple[tuple[tuple[int, int, int], tuple[tuple[float, float, float], ...]], ...] = (
    (
        (1, 0, 0),
        ((1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (1.0, 1.0, 1.0), (1.0, 0.0, 1.0)),
    ),
    (
        (-1, 0, 0),
        ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 1.0), (0.0, 1.0, 0.0)),
    ),
    (
        (0, 1, 0),
        ((0.0, 1.0, 0.0), (0.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 0.0)),
    ),
    (
        (0, -1, 0),
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0)),
    ),
    (
        (0, 0, 1),
        ((0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0)),
    ),
    (
        (0, 0, -1),
        ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    ),
)


@dataclass(frozen=True)
class OccupiedVoxel:
    world: tuple[int, int, int]
    token: str
    layer_list_index: int
    local_x: int
    local_z: int


@dataclass(frozen=True)
class OrbitMeshData:
    """Combined mesh for one draw call (positions, normals, optional atlas UVs)."""

    positions: tuple[float, ...]
    normals: tuple[float, ...]
    colors: tuple[float, ...]
    uvs: tuple[float, ...]
    tile_rects: tuple[float, ...]
    atlas_rgba: bytes | None
    atlas_width: int
    atlas_height: int
    vertex_count: int
    bounds_center: tuple[float, float, float]
    bounds_radius: float
    triangle_count: int
    offset_x: int = 0
    offset_z: int = 0
    hud_voxel_map: tuple[tuple[tuple[int, int, int], str], ...] = ()

    @property
    def uses_texture_atlas(self) -> bool:
        return self.atlas_rgba is not None and self.atlas_width > 0 and len(self.tile_rects) > 0

    def hud_voxel_dict(self) -> dict[tuple[int, int, int], str]:
        return dict(self.hud_voxel_map)


def _token_color(token: str) -> tuple[float, float, float]:
    digest = sum(ord(char) for char in token) % 360
    hue = digest / 360.0
    saturation = 0.45
    value = 0.82
    return _hsv_to_rgb(hue, saturation, value)


def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[float, float, float]:
    if s <= 0.0:
        return v, v, v
    sector = int(h * 6.0)
    fraction = h * 6.0 - sector
    p = v * (1.0 - s)
    q = v * (1.0 - s * fraction)
    t = v * (1.0 - s * (1.0 - fraction))
    if sector % 6 == 0:
        return v, t, p
    if sector % 6 == 1:
        return q, v, p
    if sector % 6 == 2:
        return p, v, t
    if sector % 6 == 3:
        return p, q, v
    if sector % 6 == 4:
        return t, p, v
    return v, p, q


def iter_occupied_voxels(
    ctx: SchematicContext,
) -> list[tuple[tuple[int, int, int], str]]:
    offset_x = get_offset_x(ctx)
    offset_z = get_offset_z(ctx)
    occupied: list[tuple[tuple[int, int, int], str]] = []

    for layer_array_index, layer in enumerate(ctx.layers):
        if not is_layer_render_visible(layer, layer_array_index, ctx.grid):
            continue

        world_y = layer_worldgen_index(layer, layer_array_index)
        cells = layer.get("cells", [])

        for local_z, row in enumerate(cells):
            for local_x, token in enumerate(row):
                if token == ".":
                    continue
                occupied.append(
                    ((offset_x + local_x, world_y, offset_z + local_z), str(token)),
                )

    return occupied


def hud_voxel_entries_from_cells(
    cells: list[OccupiedVoxel],
) -> tuple[tuple[tuple[int, int, int], str], ...]:
    return tuple((cell.world, cell.token) for cell in cells)


def build_box_orbit_mesh_from_context(ctx: SchematicContext) -> OrbitMeshData:
    """C1 per-block exterior faces (baseline for greedy mesh comparisons)."""
    occupied = iter_occupied_voxels(ctx)
    voxel_map = dict(occupied)
    offset_x = get_offset_x(ctx)
    offset_z = get_offset_z(ctx)
    hud_voxel_map = tuple(occupied)

    if not voxel_map:
        return OrbitMeshData(
            positions=(),
            normals=(),
            colors=(),
            uvs=(),
            tile_rects=(),
            atlas_rgba=None,
            atlas_width=0,
            atlas_height=0,
            vertex_count=0,
            bounds_center=(0.0, 0.0, 0.0),
            bounds_radius=1.0,
            triangle_count=0,
            offset_x=offset_x,
            offset_z=offset_z,
            hud_voxel_map=hud_voxel_map,
        )

    positions: list[float] = []
    normals: list[float] = []
    colors: list[float] = []

    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")

    for (block_x, block_y, block_z), token in voxel_map.items():
        min_x = min(min_x, float(block_x))
        min_y = min(min_y, float(block_y))
        min_z = min(min_z, float(block_z))
        max_x = max(max_x, float(block_x) + 1.0)
        max_y = max(max_y, float(block_y) + 1.0)
        max_z = max(max_z, float(block_z) + 1.0)

        color = _token_color(token)

        for (nx, ny, nz), corners in _CUBE_FACES:
            neighbor = (block_x + nx, block_y + ny, block_z + nz)
            if neighbor in voxel_map:
                continue

            tri_indices = (0, 1, 2, 0, 2, 3)
            for index in tri_indices:
                corner = corners[index]
                positions.extend(
                    (
                        block_x + corner[0],
                        block_y + corner[1],
                        block_z + corner[2],
                    ),
                )
                normals.extend((float(nx), float(ny), float(nz)))
                colors.extend(color)

    center = (
        (min_x + max_x) * 0.5,
        (min_y + max_y) * 0.5,
        (min_z + max_z) * 0.5,
    )
    radius = max(
        max_x - center[0],
        max_y - center[1],
        max_z - center[2],
        1.0,
    )

    vertex_count = len(positions) // 3
    return OrbitMeshData(
        positions=tuple(positions),
        normals=tuple(normals),
        colors=tuple(colors),
        uvs=(),
        tile_rects=(),
        atlas_rgba=None,
        atlas_width=0,
        atlas_height=0,
        vertex_count=vertex_count,
        bounds_center=center,
        bounds_radius=radius,
        triangle_count=vertex_count // 3,
        offset_x=offset_x,
        offset_z=offset_z,
        hud_voxel_map=hud_voxel_map,
    )


def build_orbit_mesh_from_context(ctx: SchematicContext) -> OrbitMeshData:
    """Build one combined greedy-meshed exterior shell from schematic layers."""
    from helpers.orbit_greedy_mesh import build_orbit_greedy_mesh_from_context

    return build_orbit_greedy_mesh_from_context(ctx)
