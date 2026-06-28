"""Attachable and multi-cell orbit preview geometry (C4)."""

from __future__ import annotations

from helpers.lantern_placement import cell_supports_lantern_hang, explicit_hanging
from helpers.orbit_mesh import OccupiedVoxel
from helpers.orbit_partial_mesh import OrbitBox
from helpers.registry_blocks import get_block_behavior, resolve_token_color
from helpers.registry_lookup import get_block_entry
from helpers.sprite_baker.block_model import (
    _element_bounds,
    block_model_path,
    has_block_model,
    load_block_model,
)
from helpers.sprite_baker.compose_lantern import resolve_lantern_model_name, resolve_lantern_variant
from helpers.sprite_baker.compose_torch import resolve_torch_variant
from helpers.sprite_baker.compose_trapdoor import resolve_trapdoor_half
from helpers.structure_tokens import ParsedToken, format_structure_token, parse_structure_token
from helpers.trapdoor_state import explicit_open
from helpers.types import BlockRegistryEntry, CellGrid
from helpers.utils import normalize_direction

ATTACHABLE_BEHAVIORS = frozenset({"torch", "lantern", "bed", "chest", "trapdoor", "door"})
BLOCK_MODEL_FACE_BEHAVIORS = frozenset({"torch", "lantern", "trapdoor"})

_MODEL_SCALE = 1.0 / 16.0
_BED_HEIGHT = 9.0 / 16.0
_CHEST_HEIGHT = 14.0 / 16.0
_DOOR_THICKNESS = 3.0 / 16.0

# Y-rotation (degrees) keyed by normalize_direction() → N/S/E/W.
_BOX_Y_ROTATION = {"S": 0, "W": 90, "N": 180, "E": 270}
_WALL_TORCH_Y_ROTATION = {"E": 0, "S": 90, "W": 180, "N": 270}
_TRAPDOOR_OPEN_Y_ROTATION = {"N": 0, "E": 90, "S": 180, "W": 270}

_TORCH_MODELS = {"normal": "torch", "soul": "soul_torch", "wall": "wall_torch"}


def is_attachable_behavior(behavior: str) -> bool:
    return behavior in ATTACHABLE_BEHAVIORS


def is_block_model_face_behavior(token: str) -> bool:
    parsed = parse_structure_token(token)
    if parsed is None:
        return False
    entry = get_block_entry(parsed) or {}
    return get_block_behavior(entry) in BLOCK_MODEL_FACE_BEHAVIORS


def resolve_attachable_block_model(
    cell: OccupiedVoxel,
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
    *,
    layer_cells_cache: dict[int, CellGrid] | None = None,
) -> tuple[str, int] | None:
    """Return (model_name, rotation_y) for attachables that use JSON element faces."""
    behavior = get_block_behavior(entry)
    if behavior not in BLOCK_MODEL_FACE_BEHAVIORS:
        return None

    if behavior == "torch":
        variant = resolve_torch_variant(parsed.variant, entry)
        model_name = _TORCH_MODELS.get(variant, "torch")
        rotation = _wall_torch_rotation_y(parsed.direction) if variant == "wall" else 0
        return model_name, rotation

    if behavior == "lantern":
        model_name = _resolve_lantern_model_name(
            cell,
            entry,
            parsed,
            layer_cells_cache=layer_cells_cache,
        )
        return model_name, 0

    if behavior == "trapdoor":
        material = _trapdoor_material(parsed, entry)
        is_open = explicit_open(parsed)
        if is_open is None:
            is_open = bool(entry.get("defaults", {}).get("open", False))
        if is_open:
            return f"{material}_trapdoor_open", _trapdoor_open_rotation_y(parsed.direction)
        half = resolve_trapdoor_half(parsed.variant, entry)
        suffix = "top" if half == "top" else "bottom"
        return f"{material}_trapdoor_{suffix}", 0

    return None


def attachable_boxes_for_cell(
    cell: OccupiedVoxel,
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
    layer_cells: CellGrid,
    *,
    layer_cells_cache: dict[int, CellGrid] | None,
    cell_by_world: dict[tuple[int, int, int], OccupiedVoxel] | None,
    wx: float,
    wy: float,
    wz: float,
) -> list[OrbitBox]:
    behavior = get_block_behavior(entry)

    if behavior == "torch":
        return _torch_boxes(cell, entry, parsed, wx, wy, wz)
    if behavior == "lantern":
        return _lantern_boxes(
            cell,
            entry,
            parsed,
            wx,
            wy,
            wz,
            layer_cells_cache=layer_cells_cache,
        )
    if behavior == "bed":
        return _bed_boxes(cell, parsed, cell_by_world, wx, wy, wz)
    if behavior == "chest":
        return _chest_boxes(cell, parsed, cell_by_world, wx, wy, wz)
    if behavior == "trapdoor":
        return _trapdoor_boxes(cell, entry, parsed, wx, wy, wz)
    if behavior == "door":
        return _door_boxes(cell, parsed, wx, wy, wz)

    return _fallback_unit_box(cell, wx, wy, wz)


def _fallback_unit_box(
    cell: OccupiedVoxel,
    wx: float,
    wy: float,
    wz: float,
) -> list[OrbitBox]:
    return [
        OrbitBox(
            cell=cell,
            min_corner=(wx, wy, wz),
            max_corner=(wx + 1.0, wy + 1.0, wz + 1.0),
        ),
    ]


def _box_direction_rotation_y(direction: str | None) -> int:
    return _BOX_Y_ROTATION.get(normalize_direction(direction) or "S", 0)


def _wall_torch_rotation_y(direction: str | None) -> int:
    return _WALL_TORCH_Y_ROTATION.get(normalize_direction(direction) or "N", 0)


def _trapdoor_open_rotation_y(direction: str | None) -> int:
    return _TRAPDOOR_OPEN_Y_ROTATION.get(normalize_direction(direction) or "N", 0)


def _direction_rotation_y(direction: str | None) -> int:
    return _box_direction_rotation_y(direction)


def _boxes_from_block_model(
    cell: OccupiedVoxel,
    model_name: str,
    wx: float,
    wy: float,
    wz: float,
    *,
    rotation_y: int = 0,
) -> list[OrbitBox]:
    if not has_block_model(model_name):
        return _fallback_unit_box(cell, wx, wy, wz)

    model = load_block_model(block_model_path(model_name))
    boxes: list[OrbitBox] = []

    for element in model.get("elements", []):
        x1, y1, z1, x2, y2, z2 = _element_bounds(element, rotation_y)
        boxes.append(
            OrbitBox(
                cell=cell,
                min_corner=(
                    wx + x1 * _MODEL_SCALE,
                    wy + y1 * _MODEL_SCALE,
                    wz + z1 * _MODEL_SCALE,
                ),
                max_corner=(
                    wx + x2 * _MODEL_SCALE,
                    wy + y2 * _MODEL_SCALE,
                    wz + z2 * _MODEL_SCALE,
                ),
            ),
        )

    return boxes


def _rotate_boxes_for_direction(
    boxes: list[OrbitBox],
    direction: str | None,
    wx: float,
    wy: float,
    wz: float,
) -> list[OrbitBox]:
    degrees = _direction_rotation_y(direction)
    if degrees == 0:
        return boxes
    from helpers.orbit_partial_mesh import _rotate_orbit_box_xz

    return [_rotate_orbit_box_xz(box, degrees, wx, wy, wz) for box in boxes]


def _torch_boxes(
    cell: OccupiedVoxel,
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
    wx: float,
    wy: float,
    wz: float,
) -> list[OrbitBox]:
    variant = resolve_torch_variant(parsed.variant, entry)
    model_name = _TORCH_MODELS.get(variant, "torch")
    rotation = _wall_torch_rotation_y(parsed.direction) if variant == "wall" else 0
    return _boxes_from_block_model(cell, model_name, wx, wy, wz, rotation_y=rotation)


def _lantern_boxes(
    cell: OccupiedVoxel,
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
    wx: float,
    wy: float,
    wz: float,
    *,
    layer_cells_cache: dict[int, CellGrid] | None,
) -> list[OrbitBox]:
    model_name = _resolve_lantern_model_name(
        cell,
        entry,
        parsed,
        layer_cells_cache=layer_cells_cache,
    )
    return _boxes_from_block_model(cell, model_name, wx, wy, wz)


def _resolve_lantern_model_name(
    cell: OccupiedVoxel,
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
    *,
    layer_cells_cache: dict[int, CellGrid] | None,
) -> str:
    variant = resolve_lantern_variant(parsed.variant, entry)
    model_name = resolve_lantern_model_name(entry, variant)
    hanging = explicit_hanging(parsed)
    if hanging is None and layer_cells_cache is not None:
        hanging = _infer_lantern_hanging(cell, layer_cells_cache)
    if hanging:
        hanging_name = f"{model_name}_hanging"
        if has_block_model(hanging_name):
            return hanging_name
        if has_block_model("lantern_hanging"):
            return "lantern_hanging"
    return model_name


def _infer_lantern_hanging(
    cell: OccupiedVoxel,
    layer_cells_cache: dict[int, CellGrid],
) -> bool:
    above_cells = layer_cells_cache.get(cell.layer_list_index + 1)
    if not above_cells:
        return False
    if cell.local_z >= len(above_cells):
        return False
    row = above_cells[cell.local_z]
    if cell.local_x >= len(row):
        return False
    return cell_supports_lantern_hang(row[cell.local_x])


def _bed_boxes(
    cell: OccupiedVoxel,
    parsed: ParsedToken,
    cell_by_world: dict[tuple[int, int, int], OccupiedVoxel] | None,
    wx: float,
    wy: float,
    wz: float,
) -> list[OrbitBox]:
    part = parsed.variant or "head"

    if part == "foot" and _bed_has_partner(cell, parsed, cell_by_world, want="head"):
        return []

    partner_offset = _bed_partner_offset(cell, parsed, cell_by_world)
    if part == "head" and partner_offset is not None:
        dx, _, dz = partner_offset
        min_x, max_x = wx, wx + 1.0
        min_z, max_z = wz, wz + 1.0
        if dx > 0:
            max_x = wx + 2.0
        elif dx < 0:
            min_x = wx - 1.0
        if dz > 0:
            max_z = wz + 2.0
        elif dz < 0:
            min_z = wz - 1.0
        return [
            OrbitBox(
                cell=cell,
                min_corner=(min_x, wy, min_z),
                max_corner=(max_x, wy + _BED_HEIGHT, max_z),
                role="bed",
                bed_span=(dx, dz),
            ),
        ]

    return _single_bed_box(cell, wx, wy, wz)


def _bed_has_partner(
    cell: OccupiedVoxel,
    parsed: ParsedToken,
    cell_by_world: dict[tuple[int, int, int], OccupiedVoxel] | None,
    *,
    want: str,
) -> bool:
    return _bed_partner_offset(cell, parsed, cell_by_world, want=want) is not None


def _bed_partner_offset(
    cell: OccupiedVoxel,
    parsed: ParsedToken,
    cell_by_world: dict[tuple[int, int, int], OccupiedVoxel] | None,
    *,
    want: str | None = None,
) -> tuple[int, int, int] | None:
    if cell_by_world is None:
        return None

    part = parsed.variant or "head"
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        partner = cell_by_world.get((cell.world[0] + dx, cell.world[1], cell.world[2] + dz))
        if partner is None:
            continue
        partner_parsed = parse_structure_token(partner.token)
        if partner_parsed is None or partner_parsed.token != "BED":
            continue
        if normalize_direction(partner_parsed.direction) != normalize_direction(parsed.direction):
            continue
        partner_part = partner_parsed.variant or "head"
        if want is not None and partner_part != want:
            continue
        if part == "head" and partner_part != "foot":
            continue
        if part == "foot" and partner_part != "head":
            continue
        if not tokens_match_bed_partner(parsed, partner_parsed):
            continue
        return (dx, 0, dz)

    return None


def _single_bed_box(
    cell: OccupiedVoxel,
    wx: float,
    wy: float,
    wz: float,
) -> list[OrbitBox]:
    return [
        OrbitBox(
            cell=cell,
            min_corner=(wx, wy, wz),
            max_corner=(wx + 1.0, wy + _BED_HEIGHT, wz + 1.0),
            role="bed",
        ),
    ]


def _chest_boxes(
    cell: OccupiedVoxel,
    parsed: ParsedToken,
    cell_by_world: dict[tuple[int, int, int], OccupiedVoxel] | None,
    wx: float,
    wy: float,
    wz: float,
) -> list[OrbitBox]:
    part = parsed.variant or "single"

    if part == "right" and _chest_has_partner(cell, parsed, cell_by_world, want="left"):
        return []

    partner_offset = _chest_partner_offset(cell, parsed, cell_by_world)
    if part == "left" and partner_offset is not None:
        dx, _, dz = partner_offset
        min_x, max_x = wx, wx + 1.0
        min_z, max_z = wz, wz + 1.0
        if dx > 0:
            max_x = wx + 2.0
        elif dx < 0:
            min_x = wx - 1.0
        if dz > 0:
            max_z = wz + 2.0
        elif dz < 0:
            min_z = wz - 1.0
        return [
            OrbitBox(
                cell=cell,
                min_corner=(min_x, wy, min_z),
                max_corner=(max_x, wy + _CHEST_HEIGHT, max_z),
                role="chest",
            ),
        ]

    return [
        OrbitBox(
            cell=cell,
            min_corner=(wx, wy, wz),
            max_corner=(wx + 1.0, wy + _CHEST_HEIGHT, wz + 1.0),
            role="chest",
        ),
    ]


def _chest_has_partner(
    cell: OccupiedVoxel,
    parsed: ParsedToken,
    cell_by_world: dict[tuple[int, int, int], OccupiedVoxel] | None,
    *,
    want: str,
) -> bool:
    return _chest_partner_offset(cell, parsed, cell_by_world, want=want) is not None


def _chest_partner_offset(
    cell: OccupiedVoxel,
    parsed: ParsedToken,
    cell_by_world: dict[tuple[int, int, int], OccupiedVoxel] | None,
    *,
    want: str | None = None,
) -> tuple[int, int, int] | None:
    if cell_by_world is None:
        return None

    part = parsed.variant or "single"
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        partner = cell_by_world.get((cell.world[0] + dx, cell.world[1], cell.world[2] + dz))
        if partner is None:
            continue
        partner_parsed = parse_structure_token(partner.token)
        if partner_parsed is None or partner_parsed.token != "CHEST":
            continue
        if normalize_direction(partner_parsed.direction) != normalize_direction(parsed.direction):
            continue
        partner_part = partner_parsed.variant or "single"
        if want is not None and partner_part != want:
            continue
        if part == "left" and partner_part != "right":
            continue
        if part == "right" and partner_part != "left":
            continue
        return (dx, 0, dz)

    return None


def _trapdoor_material(parsed: ParsedToken, entry: BlockRegistryEntry) -> str:
    return parsed.material or entry.get("material_default") or "oak"


def _trapdoor_boxes(
    cell: OccupiedVoxel,
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
    wx: float,
    wy: float,
    wz: float,
) -> list[OrbitBox]:
    material = _trapdoor_material(parsed, entry)
    direction = parsed.direction
    is_open = explicit_open(parsed)
    if is_open is None:
        is_open = bool(entry.get("defaults", {}).get("open", False))

    if is_open:
        model_name = f"{material}_trapdoor_open"
        boxes = _boxes_from_block_model(cell, model_name, wx, wy, wz)
        return _rotate_boxes_for_direction(boxes, direction, wx, wy, wz)

    half = resolve_trapdoor_half(parsed.variant, entry)
    suffix = "top" if half == "top" else "bottom"
    model_name = f"{material}_trapdoor_{suffix}"
    return _boxes_from_block_model(cell, model_name, wx, wy, wz)


def _door_boxes(
    cell: OccupiedVoxel,
    parsed: ParsedToken,
    wx: float,
    wy: float,
    wz: float,
) -> list[OrbitBox]:
    # Lower/upper variants are separate layer cells (each 1 block tall), not two
    # half-plates in one cell — see residence stage1 L1 #lower + L2 #upper.
    plate = OrbitBox(
        cell=cell,
        min_corner=(wx, wy, wz + 1.0 - _DOOR_THICKNESS),
        max_corner=(wx + 1.0, wy + 1.0, wz + 1.0),
        role="door",
    )
    return _rotate_boxes_for_direction([plate], parsed.direction, wx, wy, wz)


def tokens_match_bed_partner(left: ParsedToken, right: ParsedToken) -> bool:
    """Return whether two parsed bed tokens form a pair (color + facing)."""
    if left.token != "BED" or right.token != "BED":
        return False
    if normalize_direction(left.direction) != normalize_direction(right.direction):
        return False
    left_entry = get_block_entry(left) or {}
    right_entry = get_block_entry(right) or {}
    return resolve_token_color(left_entry, left) == resolve_token_color(right_entry, right)


def bed_foot_token(head_token: str) -> str:
    """Return the foot-part token paired with a head bed token."""
    parsed = parse_structure_token(head_token)
    if parsed is None or parsed.token != "BED":
        return head_token
    if parsed.variant == "foot":
        return head_token

    from dataclasses import replace

    return format_structure_token(replace(parsed, variant="foot"))
