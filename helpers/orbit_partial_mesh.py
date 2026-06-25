"""Partial-block axis-aligned boxes for the 3D orbit preview (C3b)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from helpers.context import SchematicContext
from helpers.fence_adjacency import classify_fence_variant, resolve_fence_connections
from helpers.orbit_mesh import OccupiedVoxel
from helpers.registry_blocks import get_block_behavior
from helpers.registry_lookup import get_block_entry
from helpers.sprite_baker.compose_slab import resolve_slab_placement
from helpers.sprite_baker.compose_stairs import resolve_stair_shape
from helpers.structure_tokens import ParsedToken, parse_structure_token
from helpers.types import BlockRegistryEntry, CellGrid
from helpers.utils import normalize_direction
from helpers.utils_schematics import corner_stair_facing_rotation

PARTIAL_BEHAVIORS = frozenset({"slab", "stairs", "fence", "wall"})

POST_MIN = 0.375
POST_MAX = 0.625
ARM_THICKNESS = 0.125
STAIR_RISER_THICKNESS = 0.125


@dataclass(frozen=True)
class OrbitBox:
    cell: OccupiedVoxel
    min_corner: tuple[float, float, float]
    max_corner: tuple[float, float, float]
    role: str = "default"


def build_orbit_partial_mesh_from_context(ctx: SchematicContext):
    """Build orbit mesh including partial-block geometry (delegates to greedy builder)."""
    from helpers.orbit_greedy_mesh import build_orbit_greedy_mesh_from_context

    return build_orbit_greedy_mesh_from_context(ctx)


def is_partial_behavior(token: str) -> bool:
    parsed = parse_structure_token(token)
    if parsed is None:
        return False
    entry = get_block_entry(parsed) or {}
    return get_block_behavior(entry) in PARTIAL_BEHAVIORS


def iter_orbit_boxes_for_cell(
    cell: OccupiedVoxel,
    layer_cells: CellGrid,
) -> list[OrbitBox]:
    parsed = parse_structure_token(cell.token)
    if parsed is None:
        return _full_block_box(cell)

    entry = get_block_entry(parsed) or {}
    behavior = get_block_behavior(entry)
    wx, wy, wz = (float(cell.world[0]), float(cell.world[1]), float(cell.world[2]))

    if behavior == "slab":
        return _slab_boxes(cell, entry, parsed, wx, wy, wz)
    if behavior == "stairs":
        return _stair_boxes(cell, entry, parsed, wx, wy, wz)
    if behavior in {"fence", "wall"}:
        return _fence_boxes(cell, layer_cells, wx, wy, wz)

    return _full_block_box(cell)


def iter_all_orbit_boxes(
    cells: list[OccupiedVoxel],
    layer_cells_cache: dict[int, CellGrid],
) -> list[OrbitBox]:
    boxes: list[OrbitBox] = []
    for cell in cells:
        layer_cells = layer_cells_cache.get(cell.layer_list_index, [])
        boxes.extend(iter_orbit_boxes_for_cell(cell, layer_cells))
    return boxes


def _full_block_box(cell: OccupiedVoxel) -> list[OrbitBox]:
    wx, wy, wz = cell.world
    return [
        OrbitBox(
            cell=cell,
            min_corner=(float(wx), float(wy), float(wz)),
            max_corner=(float(wx + 1), float(wy + 1), float(wz + 1)),
        ),
    ]


def _slab_boxes(cell, entry, parsed, wx, wy, wz) -> list[OrbitBox]:
    placement = resolve_slab_placement(parsed.variant, entry)
    if placement == "top":
        return [
            OrbitBox(
                cell=cell,
                min_corner=(wx, wy + 0.5, wz),
                max_corner=(wx + 1.0, wy + 1.0, wz + 1.0),
            ),
        ]
    return [
        OrbitBox(
            cell=cell,
            min_corner=(wx, wy, wz),
            max_corner=(wx + 1.0, wy + 0.5, wz + 1.0),
        ),
    ]


def _stair_boxes(cell, entry, parsed, wx, wy, wz) -> list[OrbitBox]:
    shape = resolve_stair_shape(parsed.variant, entry)
    lower = OrbitBox(
        cell=cell,
        min_corner=(wx, wy, wz),
        max_corner=(wx + 1.0, wy + 0.5, wz + 1.0),
        role="lower",
    )
    upper = _stair_upper_box(cell, shape, wx, wy, wz)
    boxes = [lower, upper]
    boxes = _mirror_stair_boxes_local_z(boxes, wz)

    direction = normalize_direction(parsed.direction or entry.get("defaults", {}).get("direction"))
    boxes = _rotate_stair_boxes_for_direction(boxes, direction, wx, wy, wz)

    if _resolve_stair_half(parsed, entry) == "top":
        boxes = _flip_stair_boxes_for_half(boxes, wy)

    tread = _stair_tread_box(boxes)
    if shape == "straight":
        riser = _straight_stair_riser_box(cell, tread)
        if riser is not None:
            boxes.append(riser)

    return boxes


def _stair_tread_box(boxes: list[OrbitBox]) -> OrbitBox:
    """Upper tread box after transforms (excludes lower slab and riser strip)."""
    treads = [box for box in boxes if box.role == "tread"]
    if len(treads) != 1:
        raise ValueError(f"expected one stair tread box, found {len(treads)}")
    return treads[0]


def _straight_stair_riser_box(cell: OccupiedVoxel, upper: OrbitBox) -> OrbitBox | None:
    """Thin tread-edge box closing the L-void from the open half (straight stairs only)."""
    wx, _, wz = (float(cell.world[0]), float(cell.world[1]), float(cell.world[2]))
    umn, umx = upper.min_corner, upper.max_corner
    mid_x = wx + 0.5
    mid_z = wz + 0.5
    thickness = STAIR_RISER_THICKNESS

    covers_low_x = umn[0] < mid_x - 1e-6
    covers_high_x = umx[0] > mid_x + 1e-6
    covers_low_z = umn[2] < mid_z - 1e-6
    covers_high_z = umx[2] > mid_z + 1e-6
    y0, y1 = umn[1], umx[1]

    if covers_high_z and not covers_low_z:
        return OrbitBox(
            cell=cell,
            min_corner=(umn[0], y0, umn[2]),
            max_corner=(umx[0], y1, umn[2] + thickness),
            role="riser",
        )
    if covers_low_z and not covers_high_z:
        return OrbitBox(
            cell=cell,
            min_corner=(umn[0], y0, umx[2] - thickness),
            max_corner=(umx[0], y1, umx[2]),
            role="riser",
        )
    if covers_high_x and not covers_low_x:
        return OrbitBox(
            cell=cell,
            min_corner=(umn[0], y0, umn[2]),
            max_corner=(umn[0] + thickness, y1, umx[2]),
            role="riser",
        )
    if covers_low_x and not covers_high_x:
        return OrbitBox(
            cell=cell,
            min_corner=(umx[0] - thickness, y0, umn[2]),
            max_corner=(umx[0], y1, umx[2]),
            role="riser",
        )
    return None


def _resolve_stair_half(parsed: ParsedToken, entry: BlockRegistryEntry) -> str:
    for key, value in parsed.states:
        if key == "half":
            return str(value).lower()

    return str(entry.get("defaults", {}).get("half", "bottom")).lower()


def _mirror_stair_boxes_local_z(boxes: list[OrbitBox], wz: float) -> list[OrbitBox]:
    """Flip south-authored boxes on Z so treads match 2D top-down masks (+z = south)."""
    mirrored: list[OrbitBox] = []

    for box in boxes:
        local_min_z = box.min_corner[2] - wz
        local_max_z = box.max_corner[2] - wz
        mirrored.append(
            OrbitBox(
                cell=box.cell,
                min_corner=(box.min_corner[0], box.min_corner[1], wz + (1.0 - local_max_z)),
                max_corner=(box.max_corner[0], box.max_corner[1], wz + (1.0 - local_min_z)),
                role=box.role,
            ),
        )

    return mirrored


def _rotate_stair_boxes_for_direction(
    boxes: list[OrbitBox],
    direction: str | None,
    wx: float,
    wy: float,
    wz: float,
) -> list[OrbitBox]:
    degrees = corner_stair_facing_rotation(direction)
    if degrees == 0:
        return boxes

    return [_rotate_orbit_box_xz(box, degrees, wx, wy, wz) for box in boxes]


def _rotate_orbit_box_xz(
    box: OrbitBox,
    degrees: int,
    wx: float,
    wy: float,
    wz: float,
) -> OrbitBox:
    angle = math.radians(degrees)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    rotated_xs: list[float] = []
    rotated_zs: list[float] = []

    for point in _orbit_box_corners(box):
        world_x, world_z = _rotate_local_xz_point(
            point[0] - wx,
            point[2] - wz,
            cos_a,
            sin_a,
            wx,
            wz,
        )
        rotated_xs.append(world_x)
        rotated_zs.append(world_z)

    return OrbitBox(
        cell=box.cell,
        min_corner=(min(rotated_xs), box.min_corner[1], min(rotated_zs)),
        max_corner=(max(rotated_xs), box.max_corner[1], max(rotated_zs)),
        role=box.role,
    )


def _orbit_box_corners(box: OrbitBox) -> list[tuple[float, float, float]]:
    min_x, min_y, min_z = box.min_corner
    max_x, max_y, max_z = box.max_corner
    return [
        (min_x, min_y, min_z),
        (max_x, min_y, min_z),
        (min_x, max_y, min_z),
        (max_x, max_y, min_z),
        (min_x, min_y, max_z),
        (max_x, min_y, max_z),
        (min_x, max_y, max_z),
        (max_x, max_y, max_z),
    ]


def _rotate_local_xz_point(
    local_x: float,
    local_z: float,
    cos_a: float,
    sin_a: float,
    wx: float,
    wz: float,
) -> tuple[float, float]:
    dx = local_x - 0.5
    dz = local_z - 0.5
    rotated_x = 0.5 + (dx * cos_a) - (dz * sin_a)
    rotated_z = 0.5 + (dx * sin_a) + (dz * cos_a)
    return (wx + rotated_x, wz + rotated_z)


def _flip_stair_boxes_for_half(boxes: list[OrbitBox], wy: float) -> list[OrbitBox]:
    flipped: list[OrbitBox] = []

    for box in boxes:
        local_min_y = box.min_corner[1] - wy
        local_max_y = box.max_corner[1] - wy
        flipped.append(
            OrbitBox(
                cell=box.cell,
                min_corner=(
                    box.min_corner[0],
                    wy + (1.0 - local_max_y),
                    box.min_corner[2],
                ),
                max_corner=(
                    box.max_corner[0],
                    wy + (1.0 - local_min_y),
                    box.max_corner[2],
                ),
                role=box.role,
            ),
        )

    return flipped


def _stair_upper_box(cell, shape: str, wx, wy, wz) -> OrbitBox:
    # South-facing schematic masks; mirrored on Z before rotation (see _mirror_stair_boxes_local_z).
    if shape == "straight":
        return OrbitBox(
            cell=cell,
            min_corner=(wx, wy + 0.5, wz),
            max_corner=(wx + 1.0, wy + 1.0, wz + 0.5),
            role="tread",
        )
    if shape == "outer_left":
        return OrbitBox(
            cell=cell,
            min_corner=(wx + 0.5, wy + 0.5, wz),
            max_corner=(wx + 1.0, wy + 1.0, wz + 0.5),
            role="tread",
        )
    if shape == "outer_right":
        return OrbitBox(
            cell=cell,
            min_corner=(wx, wy + 0.5, wz),
            max_corner=(wx + 0.5, wy + 1.0, wz + 0.5),
            role="tread",
        )
    if shape == "inner_left":
        return OrbitBox(
            cell=cell,
            min_corner=(wx, wy + 0.5, wz + 0.5),
            max_corner=(wx + 0.5, wy + 1.0, wz + 1.0),
            role="tread",
        )
    return OrbitBox(
        cell=cell,
        min_corner=(wx + 0.5, wy + 0.5, wz + 0.5),
        max_corner=(wx + 1.0, wy + 1.0, wz + 1.0),
        role="tread",
    )


def _fence_boxes(cell, layer_cells: CellGrid, wx, wy, wz) -> list[OrbitBox]:
    connections = resolve_fence_connections(layer_cells, cell.local_x, cell.local_z)
    variant = classify_fence_variant(connections)
    boxes: list[OrbitBox] = [
        OrbitBox(
            cell=cell,
            min_corner=(wx + POST_MIN, wy, wz + POST_MIN),
            max_corner=(wx + POST_MAX, wy + 1.0, wz + POST_MAX),
        ),
    ]

    if variant in {"end", "straight", "corner", "tee", "cross"}:
        for direction in connections:
            boxes.append(_fence_arm_box(cell, wx, wy, wz, direction))

    return boxes


def _fence_arm_box(cell, wx, wy, wz, direction: str) -> OrbitBox:
    center_min = wx + POST_MIN
    center_max = wx + POST_MAX
    z_min = wz + POST_MIN
    z_max = wz + POST_MAX

    if direction == "north":
        return OrbitBox(
            cell=cell,
            min_corner=(center_min, wy, wz),
            max_corner=(center_max, wy + 1.0, z_min),
        )
    if direction == "south":
        return OrbitBox(
            cell=cell,
            min_corner=(center_min, wy, z_max),
            max_corner=(center_max, wy + 1.0, wz + 1.0),
        )
    if direction == "east":
        return OrbitBox(
            cell=cell,
            min_corner=(center_max, wy, z_min),
            max_corner=(wx + 1.0, wy + 1.0, z_max),
        )
    return OrbitBox(
        cell=cell,
        min_corner=(wx, wy, z_min),
        max_corner=(center_min, wy + 1.0, z_max),
    )


def group_orbit_boxes_by_world(
    all_boxes: list[OrbitBox],
) -> dict[tuple[int, int, int], list[OrbitBox]]:
    """Group orbit boxes by their structure cell world coordinate."""
    grouped: dict[tuple[int, int, int], list[OrbitBox]] = {}

    for box in all_boxes:
        grouped.setdefault(box.cell.world, []).append(box)

    return grouped


def _is_bottom_slab_box(box: OrbitBox) -> bool:
    parsed = parse_structure_token(box.cell.token)
    if parsed is None:
        return False

    entry = get_block_entry(parsed) or {}
    if get_block_behavior(entry) != "slab":
        return False

    if resolve_slab_placement(parsed.variant, entry) != "bottom":
        return False

    wy = float(box.cell.world[1])
    return abs(box.min_corner[1] - wy) < 1e-6 and abs(box.max_corner[1] - (wy + 0.5)) < 1e-6


def _is_top_slab_box(box: OrbitBox) -> bool:
    parsed = parse_structure_token(box.cell.token)
    if parsed is None:
        return False

    entry = get_block_entry(parsed) or {}
    if get_block_behavior(entry) != "slab":
        return False

    if resolve_slab_placement(parsed.variant, entry) != "top":
        return False

    wy = float(box.cell.world[1])
    return abs(box.min_corner[1] - (wy + 0.5)) < 1e-6 and abs(box.max_corner[1] - (wy + 1.0)) < 1e-6


def solid_face_strip_half_toward_neighbor(
    boxes_by_world: dict[tuple[int, int, int], list[OrbitBox]],
    neighbor_world: tuple[int, int, int],
) -> Literal["upper", "lower"] | None:
    """Which vertical strip of a solid face stays visible beside a half-slab neighbor."""
    boxes = boxes_by_world.get(neighbor_world)
    if not boxes:
        return None

    for box in boxes:
        if _is_bottom_slab_box(box):
            return "upper"
        if _is_top_slab_box(box):
            return "lower"

    return None


def _slab_behavior(box: OrbitBox) -> bool:
    parsed = parse_structure_token(box.cell.token)
    if parsed is None:
        return False

    entry = get_block_entry(parsed) or {}
    return get_block_behavior(entry) == "slab"


def _slab_deck_bottom_face_occluded(
    box: OrbitBox,
    boxes_by_world: dict[tuple[int, int, int], list[OrbitBox]],
) -> bool:
    """Cull −Y on bottom slabs that form a horizontal deck with empty space below."""
    if not _is_bottom_slab_box(box):
        return False

    wx, wy, wz = box.cell.world
    below_world = (wx, wy - 1, wz)
    if boxes_by_world.get(below_world):
        return False

    token = box.cell.token
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for neighbor_box in boxes_by_world.get((wx + dx, wy, wz + dz), ()):
            if neighbor_box.cell.token != token:
                continue
            if _is_bottom_slab_box(neighbor_box):
                return True

    return False


def point_inside_box(point: tuple[float, float, float], box: OrbitBox) -> bool:
    px, py, pz = point
    min_x, min_y, min_z = box.min_corner
    max_x, max_y, max_z = box.max_corner
    return min_x <= px <= max_x and min_y <= py <= max_y and min_z <= pz <= max_z


def box_face_occluded(
    box: OrbitBox,
    normal: tuple[int, int, int],
    all_boxes: list[OrbitBox],
    *,
    skip_index: int,
    boxes_by_world: dict[tuple[int, int, int], list[OrbitBox]] | None = None,
) -> bool:
    if (
        boxes_by_world is not None
        and normal == (0, -1, 0)
        and _slab_deck_bottom_face_occluded(box, boxes_by_world)
    ):
        return True

    probes = _face_probe_points(box, normal)
    for probe in probes:
        if not _probe_occluded(
            box,
            normal,
            probe,
            all_boxes,
            skip_index=skip_index,
            boxes_by_world=boxes_by_world,
        ):
            return False
    return True


def _probe_occluded(
    box: OrbitBox,
    normal: tuple[int, int, int],
    probe: tuple[float, float, float],
    all_boxes: list[OrbitBox],
    *,
    skip_index: int,
    boxes_by_world: dict[tuple[int, int, int], list[OrbitBox]] | None = None,
) -> bool:
    for index, other in enumerate(all_boxes):
        if index == skip_index:
            continue
        if other.cell.world != box.cell.world:
            continue
        if point_inside_box(probe, other):
            return True
        if _coplanar_top_face_occluded(box, other, normal, probe):
            return True

    if boxes_by_world is not None and _slab_behavior(box):
        return _neighbor_box_occludes_probe(box, normal, probe, boxes_by_world)

    return False


def _neighbor_box_occludes_probe(
    box: OrbitBox,
    normal: tuple[int, int, int],
    probe: tuple[float, float, float],
    boxes_by_world: dict[tuple[int, int, int], list[OrbitBox]],
) -> bool:
    wx, wy, wz = box.cell.world
    nx, ny, nz = normal
    neighbor_world = (wx + nx, wy + ny, wz + nz)

    return any(point_inside_box(probe, other) for other in boxes_by_world.get(neighbor_world, ()))


def _is_stair_riser_box(box: OrbitBox) -> bool:
    return box.role == "riser"


def _face_probe_points(
    box: OrbitBox,
    normal: tuple[int, int, int],
) -> tuple[tuple[float, float, float], ...]:
    if normal[1] == 0:
        return (_face_probe_point(box, normal),)

    eps = 1e-4
    nx, ny, nz = normal
    offsets = (
        (nx * eps, ny * eps, nz * eps),
        (nx * eps, ny * eps, nz * eps),
        (nx * eps, ny * eps, nz * eps),
        (nx * eps, ny * eps, nz * eps),
    )
    return tuple(
        (
            corner[0] + offset[0],
            corner[1] + offset[1],
            corner[2] + offset[2],
        )
        for corner, offset in zip(_box_face_corners(box, normal), offsets, strict=True)
    )


def _coplanar_top_face_occluded(
    box: OrbitBox,
    other: OrbitBox,
    normal: tuple[int, int, int],
    probe: tuple[float, float, float],
) -> bool:
    """Drop duplicate +Y when a same-cell upper neighbor shares the tread top plane."""
    if normal != (0, 1, 0):
        return False
    if abs(box.max_corner[1] - other.max_corner[1]) > 1e-6:
        return False
    wy = float(box.cell.world[1])
    if box.min_corner[1] < wy + 0.25 or other.min_corner[1] < wy + 0.25:
        return False
    px, _, pz = probe
    return (
        other.min_corner[0] <= px <= other.max_corner[0]
        and other.min_corner[2] <= pz <= other.max_corner[2]
    )


def _face_probe_point(box: OrbitBox, normal: tuple[int, int, int]) -> tuple[float, float, float]:
    nx, ny, nz = normal
    min_x, min_y, min_z = box.min_corner
    max_x, max_y, max_z = box.max_corner
    eps = 1e-4

    if nx > 0:
        return (max_x + eps, (min_y + max_y) * 0.5, (min_z + max_z) * 0.5)
    if nx < 0:
        return (min_x - eps, (min_y + max_y) * 0.5, (min_z + max_z) * 0.5)
    if ny > 0:
        return ((min_x + max_x) * 0.5, max_y + eps, (min_z + max_z) * 0.5)
    if ny < 0:
        return ((min_x + max_x) * 0.5, min_y - eps, (min_z + max_z) * 0.5)
    if nz > 0:
        return ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, max_z + eps)
    return ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, min_z - eps)


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
