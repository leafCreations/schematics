"""Greedy mesher with catalog textures for the 3D orbit preview."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from helpers.context import SchematicContext
from helpers.grid import get_offset_x, get_offset_z
from helpers.layer_groups import is_layer_render_visible
from helpers.layer_management import layer_worldgen_index
from helpers.orbit_attachable_mesh import (
    is_block_model_face_behavior,
    resolve_attachable_block_model,
)
from helpers.orbit_block_model_mesh import (
    block_model_face_neighbor_occluded,
    iter_block_model_face_quads,
)
from helpers.orbit_face_textures import (
    orbit_face_kind_for_normal,
    pick_textures_for_face_kind,
    resolve_orbit_face_texture,
    side_facing_for_normal,
    texture_signature,
)
from helpers.orbit_mesh import ORBIT_FACE_OVERLAP, OccupiedVoxel, OrbitMeshData, _token_color
from helpers.orbit_partial_mesh import (
    OrbitBox,
    box_face_occluded,
    group_orbit_boxes_by_world,
    is_orbit_box_behavior,
    is_partial_volume_behavior,
    iter_all_orbit_boxes,
    iter_solid_neighbor_face_restore_rects,
    solid_face_strip_half_toward_neighbor,
)
from helpers.orbit_texture_atlas import OrbitAtlasLayout, OrbitTextureAtlas
from helpers.registry_lookup import get_block_entry
from helpers.structure_tokens import parse_structure_token
from helpers.types import CellGrid, MappedTextureImages

_MERGE_NONE = -1


@dataclass(frozen=True)
class _FacePass:
    normal: tuple[int, int, int]
    neighbor: tuple[int, int, int]
    u_axis: int
    v_axis: int
    fixed_axis: int
    fixed_sign: int


@dataclass(frozen=True)
class _PendingQuad:
    normal: tuple[int, int, int]
    corners: tuple[tuple[float, float, float], ...]
    atlas_id: int


_FACE_PASSES: tuple[_FacePass, ...] = (
    _FacePass((0, 1, 0), (0, 1, 0), 0, 2, 1, 1),
    _FacePass((0, -1, 0), (0, -1, 0), 0, 2, 1, -1),
    _FacePass((1, 0, 0), (1, 0, 0), 2, 1, 0, 1),
    _FacePass((-1, 0, 0), (-1, 0, 0), 2, 1, 0, -1),
    _FacePass((0, 0, 1), (0, 0, 1), 0, 1, 2, 1),
    _FacePass((0, 0, -1), (0, 0, -1), 0, 1, 2, -1),
)


def iter_occupied_voxel_cells(ctx: SchematicContext) -> list[OccupiedVoxel]:
    offset_x = get_offset_x(ctx)
    offset_z = get_offset_z(ctx)
    occupied: list[OccupiedVoxel] = []

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
                    OccupiedVoxel(
                        world=(offset_x + local_x, world_y, offset_z + local_z),
                        token=str(token),
                        layer_list_index=layer_array_index,
                        local_x=local_x,
                        local_z=local_z,
                    ),
                )

    return occupied


def greedy_merge(mask: list[list[int]]) -> list[tuple[int, int, int, int, int]]:
    """Merge a 2D grid of texture-signature ids into maximal axis-aligned rectangles."""
    if not mask:
        return []

    height = len(mask[0])
    width = len(mask)
    used = [[False] * height for _ in range(width)]
    quads: list[tuple[int, int, int, int, int]] = []

    for v in range(height):
        for u in range(width):
            signature_id = mask[u][v]
            if signature_id == _MERGE_NONE or used[u][v]:
                continue

            rect_w = 1
            while u + rect_w < width:
                next_u = u + rect_w
                if mask[next_u][v] != signature_id or used[next_u][v]:
                    break
                rect_w += 1

            rect_h = 1
            while v + rect_h < height:
                row_ok = True
                for du in range(rect_w):
                    if mask[u + du][v + rect_h] != signature_id or used[u + du][v + rect_h]:
                        row_ok = False
                        break
                if not row_ok:
                    break
                rect_h += 1

            for dv in range(rect_h):
                for du in range(rect_w):
                    used[u + du][v + dv] = True

            quads.append((u, v, rect_w, rect_h, signature_id))

    return quads


def build_orbit_greedy_mesh_from_context(ctx: SchematicContext) -> OrbitMeshData:
    """Build a greedy-meshed exterior shell with catalog textures and partial blocks.

    Per-cell dispatch taxonomy: ``helpers.orbit_render_class.orbit_render_class`` —
    ``solid_cube`` → greedy ``solid_cells``; ``partial_box`` / ``attachable_box`` /
    ``block_model`` → ``iter_all_orbit_boxes`` + partial face passes (not full cubes).
    """
    cells = iter_occupied_voxel_cells(ctx)
    if not cells:
        return _empty_mesh()

    layer_cells_cache: dict[int, CellGrid] = {
        index: ctx.layers[index].get("cells", []) for index in range(len(ctx.layers))
    }
    all_boxes = iter_all_orbit_boxes(cells, layer_cells_cache)
    boxes_by_world = group_orbit_boxes_by_world(all_boxes)
    solid_cells = [cell for cell in cells if not is_orbit_box_behavior(cell.token)]
    voxel_map = {cell.world: cell for cell in solid_cells}
    partial_worlds = frozenset(
        cell.world for cell in cells if is_partial_volume_behavior(cell.token)
    )

    atlas = OrbitTextureAtlas()
    merge_id_to_atlas: list[int] = []
    signature_to_merge_id: dict[str, int] = {}
    pending_quads: list[_PendingQuad] = []

    min_bounds = [float("inf"), float("inf"), float("inf")]
    max_bounds = [float("-inf"), float("-inf"), float("-inf")]
    _expand_bounds_from_boxes(all_boxes, min_bounds, max_bounds)

    for face_pass in _FACE_PASSES:
        _collect_solid_face_pass(
            face_pass,
            voxel_map,
            partial_worlds,
            layer_cells_cache,
            ctx.topdown_textures,
            ctx.sideview_textures,
            atlas,
            merge_id_to_atlas,
            signature_to_merge_id,
            min_bounds,
            max_bounds,
            pending_quads,
        )

    _collect_solid_slab_neighbor_strip_faces(
        voxel_map,
        partial_worlds,
        boxes_by_world,
        layer_cells_cache,
        ctx.topdown_textures,
        ctx.sideview_textures,
        atlas,
        merge_id_to_atlas,
        signature_to_merge_id,
        pending_quads,
    )

    _collect_block_model_element_faces(
        cells,
        voxel_map,
        layer_cells_cache,
        atlas,
        merge_id_to_atlas,
        signature_to_merge_id,
        pending_quads,
    )

    _collect_partial_box_faces(
        all_boxes,
        boxes_by_world,
        layer_cells_cache,
        ctx.topdown_textures,
        ctx.sideview_textures,
        atlas,
        merge_id_to_atlas,
        signature_to_merge_id,
        pending_quads,
    )

    layout = atlas.build()
    positions: list[float] = []
    normals: list[float] = []
    colors: list[float] = []
    uvs: list[float] = []
    tile_rects: list[float] = []

    for quad in pending_quads:
        _emit_pending_quad(quad, layout, positions, normals, colors, uvs, tile_rects)

    center = (
        (min_bounds[0] + max_bounds[0]) * 0.5,
        (min_bounds[1] + max_bounds[1]) * 0.5,
        (min_bounds[2] + max_bounds[2]) * 0.5,
    )
    radius = max(
        max_bounds[0] - center[0],
        max_bounds[1] - center[1],
        max_bounds[2] - center[2],
        1.0,
    )
    vertex_count = len(positions) // 3
    triangle_count = vertex_count // 3

    if layout is None:
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
            triangle_count=triangle_count,
        )

    return OrbitMeshData(
        positions=tuple(positions),
        normals=tuple(normals),
        colors=tuple(colors),
        uvs=tuple(uvs),
        tile_rects=tuple(tile_rects),
        atlas_rgba=layout.rgba,
        atlas_width=layout.width,
        atlas_height=layout.height,
        vertex_count=vertex_count,
        bounds_center=center,
        bounds_radius=radius,
        triangle_count=triangle_count,
    )


def _empty_mesh() -> OrbitMeshData:
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
    )


def _expand_bounds_from_boxes(
    boxes: list[OrbitBox],
    min_bounds: list[float],
    max_bounds: list[float],
) -> None:
    for box in boxes:
        min_x, min_y, min_z = box.min_corner
        max_x, max_y, max_z = box.max_corner
        min_bounds[0] = min(min_bounds[0], min_x)
        min_bounds[1] = min(min_bounds[1], min_y)
        min_bounds[2] = min(min_bounds[2], min_z)
        max_bounds[0] = max(max_bounds[0], max_x)
        max_bounds[1] = max(max_bounds[1], max_y)
        max_bounds[2] = max(max_bounds[2], max_z)


def _collect_solid_face_pass(
    face_pass: _FacePass,
    voxel_map: dict[tuple[int, int, int], OccupiedVoxel],
    partial_worlds: frozenset[tuple[int, int, int]],
    layer_cells_cache: dict[int, CellGrid],
    topdown_textures: MappedTextureImages | None,
    sideview_textures: MappedTextureImages | None,
    atlas: OrbitTextureAtlas,
    merge_id_to_atlas: list[int],
    signature_to_merge_id: dict[str, int],
    min_bounds: list[float],
    max_bounds: list[float],
    pending_quads: list[_PendingQuad],
) -> None:
    u_axis = face_pass.u_axis
    v_axis = face_pass.v_axis
    fixed_axis = face_pass.fixed_axis

    u_min = int(min_bounds[u_axis])
    u_max = int(max_bounds[u_axis]) - 1
    v_min = int(min_bounds[v_axis])
    v_max = int(max_bounds[v_axis]) - 1

    fixed_values = sorted(
        {
            cell.world[fixed_axis]
            for cell in voxel_map.values()
            if _solid_face_visible(
                cell.world,
                face_pass.neighbor,
                voxel_map,
                partial_worlds,
            )
        },
    )

    for fixed_value in fixed_values:
        width = u_max - u_min + 1
        height = v_max - v_min + 1
        mask: list[list[int]] = [[_MERGE_NONE] * height for _ in range(width)]

        for u_coord in range(u_min, u_max + 1):
            for v_coord in range(v_min, v_max + 1):
                world = [0, 0, 0]
                world[fixed_axis] = fixed_value
                world[u_axis] = u_coord
                world[v_axis] = v_coord
                world_tuple = (world[0], world[1], world[2])
                cell = voxel_map.get(world_tuple)
                if cell is None:
                    continue
                if not _solid_face_visible(
                    world_tuple,
                    face_pass.neighbor,
                    voxel_map,
                    partial_worlds,
                ):
                    continue

                merge_id = _register_face_signature(
                    cell,
                    face_pass.normal,
                    layer_cells_cache,
                    topdown_textures,
                    sideview_textures,
                    atlas,
                    merge_id_to_atlas,
                    signature_to_merge_id,
                )
                mask[u_coord - u_min][v_coord - v_min] = merge_id

        for u0, v0, rect_w, rect_h, merge_id in greedy_merge(mask):
            corners = _quad_world_corners(
                face_pass,
                fixed_value,
                u_min + u0,
                v_min + v0,
                rect_w,
                rect_h,
            )
            pending_quads.append(
                _PendingQuad(
                    normal=face_pass.normal,
                    corners=corners,
                    atlas_id=merge_id_to_atlas[merge_id],
                ),
            )


def _collect_partial_box_faces(
    all_boxes: list[OrbitBox],
    boxes_by_world: dict[tuple[int, int, int], list[OrbitBox]],
    layer_cells_cache: dict[int, CellGrid],
    topdown_textures: MappedTextureImages | None,
    sideview_textures: MappedTextureImages | None,
    atlas: OrbitTextureAtlas,
    merge_id_to_atlas: list[int],
    signature_to_merge_id: dict[str, int],
    pending_quads: list[_PendingQuad],
) -> None:
    for index, box in enumerate(all_boxes):
        if not is_orbit_box_behavior(box.cell.token):
            continue
        if is_block_model_face_behavior(box.cell.token):
            continue

        for face_pass in _FACE_PASSES:
            if box_face_occluded(
                box,
                face_pass.normal,
                all_boxes,
                skip_index=index,
                boxes_by_world=boxes_by_world,
            ):
                continue

            corners = _box_face_corners(box, face_pass.normal)
            merge_id = _register_face_signature(
                box.cell,
                face_pass.normal,
                layer_cells_cache,
                topdown_textures,
                sideview_textures,
                atlas,
                merge_id_to_atlas,
                signature_to_merge_id,
            )
            pending_quads.append(
                _PendingQuad(
                    normal=face_pass.normal,
                    corners=corners,
                    atlas_id=merge_id_to_atlas[merge_id],
                ),
            )


def _collect_block_model_element_faces(
    cells: list[OccupiedVoxel],
    voxel_map: dict[tuple[int, int, int], OccupiedVoxel],
    layer_cells_cache: dict[int, CellGrid],
    atlas: OrbitTextureAtlas,
    merge_id_to_atlas: list[int],
    signature_to_merge_id: dict[str, int],
    pending_quads: list[_PendingQuad],
) -> None:
    """Emit JSON element faces for torch/lantern/trapdoor — not 2D sprite bakes on AABBs."""
    for cell in cells:
        if not is_block_model_face_behavior(cell.token):
            continue

        parsed = parse_structure_token(cell.token)
        if parsed is None:
            continue
        entry = get_block_entry(parsed) or {}
        spec = resolve_attachable_block_model(
            cell,
            entry,
            parsed,
            layer_cells_cache=layer_cells_cache,
        )
        if spec is None:
            continue

        model_name, rotation_y = spec
        wx, wy, wz = (float(cell.world[0]), float(cell.world[1]), float(cell.world[2]))
        for face_quad in iter_block_model_face_quads(
            model_name,
            wx,
            wy,
            wz,
            rotation_y=rotation_y,
        ):
            if block_model_face_neighbor_occluded(cell, face_quad.normal, voxel_map):
                continue

            existing = signature_to_merge_id.get(face_quad.signature)
            if existing is None:
                fallback = _token_color(cell.token)
                atlas_id = atlas.register(face_quad.texture, fallback_rgb=fallback)
                merge_id = len(merge_id_to_atlas)
                merge_id_to_atlas.append(atlas_id)
                signature_to_merge_id[face_quad.signature] = merge_id
            else:
                merge_id = existing

            pending_quads.append(
                _PendingQuad(
                    normal=face_quad.normal,
                    corners=face_quad.corners,
                    atlas_id=merge_id_to_atlas[merge_id],
                ),
            )


def _collect_solid_slab_neighbor_strip_faces(
    voxel_map: dict[tuple[int, int, int], OccupiedVoxel],
    partial_worlds: frozenset[tuple[int, int, int]],
    boxes_by_world: dict[tuple[int, int, int], list[OrbitBox]],
    layer_cells_cache: dict[int, CellGrid],
    topdown_textures: MappedTextureImages | None,
    sideview_textures: MappedTextureImages | None,
    atlas: OrbitTextureAtlas,
    merge_id_to_atlas: list[int],
    signature_to_merge_id: dict[str, int],
    pending_quads: list[_PendingQuad],
) -> None:
    """Emit upper/lower vertical strips on solids beside half-height slab neighbors."""
    for world, cell in voxel_map.items():
        for normal in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
            neighbor = (
                world[0] + normal[0],
                world[1] + normal[1],
                world[2] + normal[2],
            )
            if neighbor not in partial_worlds:
                continue

            half = solid_face_strip_half_toward_neighbor(boxes_by_world, neighbor)
            if half is not None:
                corner_sets = [_solid_strip_quad_corners(world, normal, half=half)]
            else:
                corner_sets = iter_solid_neighbor_face_restore_rects(
                    world,
                    normal,
                    boxes_by_world,
                    neighbor,
                )

            for corners in corner_sets:
                merge_id = _register_face_signature(
                    cell,
                    normal,
                    layer_cells_cache,
                    topdown_textures,
                    sideview_textures,
                    atlas,
                    merge_id_to_atlas,
                    signature_to_merge_id,
                )
                pending_quads.append(
                    _PendingQuad(
                        normal=normal,
                        corners=corners,
                        atlas_id=merge_id_to_atlas[merge_id],
                    ),
                )


def _solid_strip_quad_corners(
    world: tuple[int, int, int],
    normal: tuple[int, int, int],
    *,
    half: Literal["upper", "lower"],
) -> tuple[tuple[float, float, float], ...]:
    wx, wy, wz = world
    min_y = float(wy + (0.5 if half == "upper" else 0.0))
    max_y = float(wy + (1.0 if half == "upper" else 0.5))
    min_x = float(wx)
    max_x = float(wx + 1)
    min_z = float(wz)
    max_z = float(wz + 1)

    if normal == (1, 0, 0):
        x = max_x
        return (
            (x, min_y, min_z),
            (x, max_y, min_z),
            (x, max_y, max_z),
            (x, min_y, max_z),
        )
    if normal == (-1, 0, 0):
        x = min_x
        return (
            (x, min_y, min_z),
            (x, min_y, max_z),
            (x, max_y, max_z),
            (x, max_y, min_z),
        )
    if normal == (0, 0, 1):
        z = max_z
        return (
            (min_x, min_y, z),
            (max_x, min_y, z),
            (max_x, max_y, z),
            (min_x, max_y, z),
        )
    z = min_z
    return (
        (min_x, min_y, z),
        (min_x, max_y, z),
        (max_x, max_y, z),
        (max_x, min_y, z),
    )


def _solid_face_visible(
    world: tuple[int, int, int],
    neighbor_offset: tuple[int, int, int],
    voxel_map: dict[tuple[int, int, int], OccupiedVoxel],
    partial_worlds: frozenset[tuple[int, int, int]],
) -> bool:
    cell = voxel_map.get(world)
    if cell is None:
        return False

    neighbor = (
        world[0] + neighbor_offset[0],
        world[1] + neighbor_offset[1],
        world[2] + neighbor_offset[2],
    )
    if neighbor in partial_worlds:
        return False

    neighbor_cell = voxel_map.get(neighbor)
    if neighbor_cell is None:
        return True

    return neighbor_cell.token != cell.token


def _register_face_signature(
    cell: OccupiedVoxel,
    normal: tuple[int, int, int],
    layer_cells_cache: dict[int, CellGrid],
    topdown_textures: MappedTextureImages | None,
    sideview_textures: MappedTextureImages | None,
    atlas: OrbitTextureAtlas,
    merge_id_to_atlas: list[int],
    signature_to_merge_id: dict[str, int],
) -> int:
    face_kind = orbit_face_kind_for_normal(normal)
    side_facing = side_facing_for_normal(normal)
    signature = texture_signature(cell.token, face_kind, side_facing=side_facing)

    existing = signature_to_merge_id.get(signature)
    if existing is not None:
        return existing

    textures = pick_textures_for_face_kind(
        face_kind,
        topdown_textures,
        sideview_textures,
    )
    fallback = _token_color(cell.token)
    image = None
    if textures:
        layer_cells = layer_cells_cache.get(cell.layer_list_index, [])
        image = resolve_orbit_face_texture(
            cell.token,
            textures,
            face_kind=face_kind,
            side_facing=side_facing,
            layer_cells=layer_cells,
            cell_x=cell.local_x,
            cell_z=cell.local_z,
            topdown_textures=topdown_textures,
            sideview_textures=sideview_textures,
        )

    merge_id = len(merge_id_to_atlas)
    merge_id_to_atlas.append(atlas.register(image, fallback_rgb=fallback))
    signature_to_merge_id[signature] = merge_id
    return merge_id


def _emit_pending_quad(
    quad: _PendingQuad,
    layout: OrbitAtlasLayout | None,
    positions: list[float],
    normals: list[float],
    colors: list[float],
    uvs: list[float],
    tile_rects: list[float],
) -> None:
    nx, ny, nz = quad.normal
    if layout is not None and quad.atlas_id < len(layout.uv_rects):
        u0, v0, u1, v1 = layout.uv_rects[quad.atlas_id]
        color = (1.0, 1.0, 1.0)
    else:
        u0 = v0 = u1 = v1 = 0.0
        color = _token_color(f"atlas-{quad.atlas_id}")

    expanded_corners = expand_orbit_quad_corners(quad.corners, quad.normal)
    tri_indices = (0, 1, 2, 0, 2, 3)
    for index in tri_indices:
        corner = expanded_corners[index]
        positions.extend(corner)
        normals.extend((float(nx), float(ny), float(nz)))
        colors.extend(color)
        uvs.extend((0.0, 0.0))
        tile_rects.extend((u0, v0, u1, v1))


_UV_EPS = 1e-6


def expand_orbit_quad_corners(
    corners: tuple[tuple[float, float, float], ...],
    normal: tuple[int, int, int],
) -> tuple[tuple[float, float, float], ...]:
    """Outset full-height vertical side quads; raise top edge (+Y) to meet top faces."""
    _, ny, _ = normal
    if ny != 0:
        return corners

    y_max = max(corner[1] for corner in corners)
    y_min = min(corner[1] for corner in corners)
    if (y_max - y_min) < 1.0 - _UV_EPS:
        return corners

    nx, _, nz = normal
    expanded: list[tuple[float, float, float]] = []
    for x, y, z in corners:
        if not (
            _is_integer_block_coord(x) and _is_integer_block_coord(y) and _is_integer_block_coord(z)
        ):
            expanded.append((x, y, z))
            continue
        px = x + nx * ORBIT_FACE_OVERLAP
        py = y
        pz = z + nz * ORBIT_FACE_OVERLAP
        if abs(y - y_max) < _UV_EPS:
            py += ORBIT_FACE_OVERLAP
        expanded.append((px, py, pz))
    return tuple(expanded)


def _is_integer_block_coord(value: float) -> bool:
    return abs(value - round(value)) < _UV_EPS


def _box_face_corners(
    box: OrbitBox,
    normal: tuple[int, int, int],
) -> tuple[tuple[float, float, float], ...]:
    min_x, min_y, min_z = box.min_corner
    max_x, max_y, max_z = box.max_corner

    if normal == (0, 1, 0):
        return (
            (min_x, max_y, min_z),
            (min_x, max_y, max_z),
            (max_x, max_y, max_z),
            (max_x, max_y, min_z),
        )
    if normal == (0, -1, 0):
        return (
            (min_x, min_y, min_z),
            (max_x, min_y, min_z),
            (max_x, min_y, max_z),
            (min_x, min_y, max_z),
        )
    if normal == (1, 0, 0):
        return (
            (max_x, min_y, min_z),
            (max_x, max_y, min_z),
            (max_x, max_y, max_z),
            (max_x, min_y, max_z),
        )
    if normal == (-1, 0, 0):
        return (
            (min_x, min_y, min_z),
            (min_x, min_y, max_z),
            (min_x, max_y, max_z),
            (min_x, max_y, min_z),
        )
    if normal == (0, 0, 1):
        return (
            (min_x, min_y, max_z),
            (max_x, min_y, max_z),
            (max_x, max_y, max_z),
            (min_x, max_y, max_z),
        )
    return (
        (min_x, min_y, min_z),
        (min_x, max_y, min_z),
        (max_x, max_y, min_z),
        (max_x, min_y, min_z),
    )


def _quad_world_corners(
    face_pass: _FacePass,
    fixed_value: int,
    u_origin: int,
    v_origin: int,
    rect_u: int,
    rect_v: int,
) -> tuple[tuple[float, float, float], ...]:
    u_axis = face_pass.u_axis
    v_axis = face_pass.v_axis
    fixed_axis = face_pass.fixed_axis

    def point(u_delta: int, v_delta: int) -> tuple[float, float, float]:
        coords = [0.0, 0.0, 0.0]
        coords[fixed_axis] = float(
            fixed_value + (1 if face_pass.fixed_sign > 0 else 0),
        )
        coords[u_axis] = float(u_origin + u_delta)
        coords[v_axis] = float(v_origin + v_delta)
        return coords[0], coords[1], coords[2]

    if face_pass.normal == (0, 1, 0):
        return (
            point(0, 0),
            point(0, rect_v),
            point(rect_u, rect_v),
            point(rect_u, 0),
        )
    if face_pass.normal == (0, -1, 0):
        return (
            point(0, 0),
            point(rect_u, 0),
            point(rect_u, rect_v),
            point(0, rect_v),
        )
    if face_pass.normal == (1, 0, 0):
        return (
            point(0, 0),
            point(rect_u, 0),
            point(rect_u, rect_v),
            point(0, rect_v),
        )
    if face_pass.normal == (-1, 0, 0):
        return (
            point(0, 0),
            point(0, rect_v),
            point(rect_u, rect_v),
            point(rect_u, 0),
        )
    if face_pass.normal == (0, 0, 1):
        return (
            point(0, 0),
            point(rect_u, 0),
            point(rect_u, rect_v),
            point(0, rect_v),
        )
    return (
        point(0, 0),
        point(0, rect_v),
        point(rect_u, rect_v),
        point(rect_u, 0),
    )
