"""Face-aware catalog texture resolution for the 3D orbit preview."""

from __future__ import annotations

from dataclasses import replace
from typing import Literal

import helpers.constants as constants
import helpers.utils_schematics as schematics_utils
from helpers import utils
from helpers.block_texture_load import load_block_texture_image
from helpers.facing_block_textures import load_facing_block_front_texture
from helpers.registry_blocks import get_block_behavior, resolve_minecraft_block_id
from helpers.registry_lookup import get_block_entry, load_catalog_texture_image
from helpers.sprite_baker.plank_materials import list_plank_materials
from helpers.structure_tokens import format_structure_token, parse_structure_token
from helpers.types import CellGrid, MappedTextureImages, RawToken
from registries.loader import BLOCK_TEXTURES_FOLDER, find_block_texture_path, get_render_textures

OrbitFaceKind = Literal["top", "bottom", "side"]

_SIDE_FACING_BY_NORMAL: dict[tuple[int, int, int], str] = {
    (1, 0, 0): "east",
    (-1, 0, 0): "west",
    (0, 0, 1): "south",
    (0, 0, -1): "north",
}


def orbit_face_kind_for_normal(normal: tuple[int, int, int]) -> OrbitFaceKind:
    if normal == (0, 1, 0):
        return "top"
    if normal == (0, -1, 0):
        return "bottom"
    return "side"


def side_facing_for_normal(normal: tuple[int, int, int]) -> str | None:
    return _SIDE_FACING_BY_NORMAL.get(normal)


def texture_signature(
    raw_token: RawToken,
    face_kind: OrbitFaceKind,
    *,
    side_facing: str | None,
) -> str:
    facing_part = side_facing or ""
    return f"{raw_token}|{face_kind}|{facing_part}"


_SIDE_FACING_TO_COMPASS: dict[str, str] = {
    "north": "N",
    "east": "E",
    "south": "S",
    "west": "W",
}


def resolve_orbit_face_texture(
    raw_token: RawToken,
    textures: MappedTextureImages,
    *,
    face_kind: OrbitFaceKind,
    side_facing: str | None = None,
    layer_cells: CellGrid | None = None,
    cell_x: int | None = None,
    cell_z: int | None = None,
    topdown_textures: MappedTextureImages | None = None,
    sideview_textures: MappedTextureImages | None = None,
):
    parsed = parse_structure_token(raw_token)
    entry = get_block_entry(parsed) or {} if parsed is not None else {}

    if get_block_behavior(entry) == "stairs":
        return _resolve_orbit_stair_face_texture(
            raw_token,
            textures,
            face_kind=face_kind,
            layer_cells=layer_cells,
            cell_x=cell_x,
            cell_z=cell_z,
        )

    if get_block_behavior(entry) == "slab":
        return _resolve_orbit_slab_face_texture(
            raw_token,
            textures,
            face_kind=face_kind,
            layer_cells=layer_cells,
            cell_x=cell_x,
            cell_z=cell_z,
        )

    if get_block_behavior(entry) == "facing_block":
        return _resolve_orbit_facing_block_face_texture(
            raw_token,
            textures,
            face_kind=face_kind,
            side_facing=side_facing,
            layer_cells=layer_cells,
            cell_x=cell_x,
            cell_z=cell_z,
            topdown_textures=topdown_textures,
            sideview_textures=sideview_textures,
        )

    if face_kind == "side":
        catalog_side = _resolve_orbit_catalog_block_face(raw_token, entry, "side")
        if catalog_side is not None:
            return catalog_side

    if face_kind == "top" and _uses_orbit_catalog_cap(parsed):
        catalog_top = _resolve_orbit_catalog_block_face(raw_token, entry, "top")
        if catalog_top is not None:
            return catalog_top

    token_for_resolve = _token_with_side_facing(raw_token, face_kind, side_facing)
    view: Literal["top", "side"] = "top" if face_kind in {"top", "bottom"} else "side"

    if face_kind == "bottom":
        bottom = _resolve_bottom_texture(
            token_for_resolve,
            textures,
            layer_cells=layer_cells,
            cell_x=cell_x,
            cell_z=cell_z,
        )
        if bottom is not None:
            return bottom
        catalog_bottom = _resolve_orbit_catalog_block_face(raw_token, entry, "bottom")
        if catalog_bottom is not None:
            return catalog_bottom

    return schematics_utils.resolve_cell_texture(
        token_for_resolve,
        textures,
        view=view,
        layer_cells=layer_cells,
        cell_x=cell_x,
        cell_z=cell_z,
    )


def pick_textures_for_face_kind(
    face_kind: OrbitFaceKind,
    topdown_textures: MappedTextureImages | None,
    sideview_textures: MappedTextureImages | None,
) -> MappedTextureImages | None:
    if face_kind in {"top", "bottom"}:
        return topdown_textures
    return sideview_textures


def _orbit_solid_material_face_token(raw_token: RawToken) -> RawToken:
    """Full-block tile for 3D box faces — not 2D half/L-mask bakes."""
    parsed = parse_structure_token(raw_token)
    if parsed is None:
        return raw_token

    entry = get_block_entry(parsed) or {}
    material = parsed.material or entry.get("material_default") or "oak"
    plank_materials = set(list_plank_materials(textures_dir=BLOCK_TEXTURES_FOLDER))
    if material in plank_materials:
        return f"PLANKS:{material}"

    mc_token = f"minecraft:{material}"
    try:
        mc_id = resolve_minecraft_block_id(entry, parsed)
    except Exception:
        return mc_token

    if mc_id.endswith("_stairs"):
        return mc_id[: -len("_stairs")]
    if mc_id.endswith("_slab"):
        return mc_id[: -len("_slab")]
    if mc_id.endswith("_fence"):
        return mc_id[: -len("_fence")]
    if mc_id.endswith("_wall"):
        return mc_id[: -len("_wall")]
    return mc_token


def _resolve_orbit_slab_face_texture(
    raw_token: RawToken,
    textures: MappedTextureImages,
    *,
    face_kind: OrbitFaceKind,
    layer_cells: CellGrid | None,
    cell_x: int | None,
    cell_z: int | None,
):
    """Use full solid-block tiles on box faces — not the 2D half-masked slab bake."""
    solid_token = _orbit_solid_material_face_token(raw_token)
    view: Literal["top", "side"] = "top" if face_kind in {"top", "bottom"} else "side"
    return schematics_utils.resolve_cell_texture(
        solid_token,
        textures,
        view=view,
        layer_cells=layer_cells,
        cell_x=cell_x,
        cell_z=cell_z,
    )


def _resolve_orbit_stair_face_texture(
    raw_token: RawToken,
    textures: MappedTextureImages,
    *,
    face_kind: OrbitFaceKind,
    layer_cells: CellGrid | None,
    cell_x: int | None,
    cell_z: int | None,
):
    """Use full solid-block tiles on box faces — not the 2D L-masked stair bake."""
    solid_token = _orbit_solid_material_face_token(raw_token)
    view: Literal["top", "side"] = "top" if face_kind in {"top", "bottom"} else "side"
    return schematics_utils.resolve_cell_texture(
        solid_token,
        textures,
        view=view,
        layer_cells=layer_cells,
        cell_x=cell_x,
        cell_z=cell_z,
    )


def _block_facing_compass(raw_token: RawToken, entry: dict) -> str | None:
    parsed = parse_structure_token(raw_token)
    if parsed is None:
        return None

    defaults = entry.get("defaults", {})
    direction = parsed.direction or defaults.get("direction")
    return utils.normalize_direction(direction)


def _is_front_facing_side(side_facing: str | None, block_facing: str | None) -> bool:
    if not side_facing or not block_facing:
        return False

    compass = _SIDE_FACING_TO_COMPASS.get(side_facing.lower())
    return compass == block_facing


def _textures_for_view(
    view: Literal["top", "side"],
    textures: MappedTextureImages,
    topdown_textures: MappedTextureImages | None,
    sideview_textures: MappedTextureImages | None,
) -> MappedTextureImages:
    if view == "top" and topdown_textures is not None:
        return topdown_textures
    if view == "side" and sideview_textures is not None:
        return sideview_textures
    return textures


def _resolve_orbit_facing_block_face_texture(
    raw_token: RawToken,
    textures: MappedTextureImages,
    *,
    face_kind: OrbitFaceKind,
    side_facing: str | None,
    layer_cells: CellGrid | None,
    cell_x: int | None,
    cell_z: int | None,
    topdown_textures: MappedTextureImages | None,
    sideview_textures: MappedTextureImages | None,
):
    parsed = parse_structure_token(raw_token)
    entry = get_block_entry(parsed) or {} if parsed is not None else {}
    block_facing = _block_facing_compass(raw_token, entry)

    if face_kind == "side" and side_facing:
        if _is_front_facing_side(side_facing, block_facing):
            texture_map = _textures_for_view(
                "top",
                textures,
                topdown_textures,
                sideview_textures,
            )
            front = _facing_block_orbit_front_texture(raw_token, texture_map)
            if front is not None:
                return front

        side_file = get_render_textures(entry).get("side")
        if isinstance(side_file, str):
            side_tex = _load_orbit_texture_file(side_file)
            if side_tex is not None:
                return side_tex

        view: Literal["top", "side"] = "side"
        texture_map = _textures_for_view(
            view,
            textures,
            topdown_textures,
            sideview_textures,
        )
        return schematics_utils.resolve_cell_texture(
            raw_token,
            texture_map,
            view=view,
            layer_cells=layer_cells,
            cell_x=cell_x,
            cell_z=cell_z,
        )

    if face_kind == "bottom":
        bottom = _resolve_bottom_texture(
            raw_token,
            _textures_for_view("top", textures, topdown_textures, sideview_textures),
            layer_cells=layer_cells,
            cell_x=cell_x,
            cell_z=cell_z,
        )
        if bottom is not None:
            return bottom
        cap = _resolve_facing_block_catalog_cap(raw_token, entry)
        if cap is not None:
            return cap
        return schematics_utils.resolve_cell_texture(
            raw_token,
            _textures_for_view("side", textures, topdown_textures, sideview_textures),
            view="side",
            layer_cells=layer_cells,
            cell_x=cell_x,
            cell_z=cell_z,
        )

    if face_kind == "top":
        cap = _resolve_facing_block_catalog_cap(raw_token, entry)
        if cap is not None:
            return cap

    return schematics_utils.resolve_cell_texture(
        raw_token,
        _textures_for_view("top", textures, topdown_textures, sideview_textures),
        view="top",
        layer_cells=layer_cells,
        cell_x=cell_x,
        cell_z=cell_z,
    )


def _resolve_facing_block_catalog_cap(raw_token: RawToken, entry: dict):
    """Orbit ±Y cap — catalog block top (not ``render.top`` front sprite for 2D)."""
    return _resolve_orbit_catalog_block_face(raw_token, entry, "top")


def _load_orbit_texture_file(filename: str):
    texture_path = find_block_texture_path(BLOCK_TEXTURES_FOLDER, filename)
    if texture_path is None:
        return None

    return load_block_texture_image(texture_path, constants.BLOCK_PX)


def _facing_block_orbit_front_texture(
    raw_token: RawToken,
    textures: MappedTextureImages,
):
    """Front sprite on a vertical face — upright; no 2D top-down direction spin."""
    parsed = parse_structure_token(raw_token)
    if parsed is None:
        return None

    entry = get_block_entry(parsed) or {}
    tex = load_facing_block_front_texture(raw_token, entry, constants.BLOCK_PX)
    if tex is not None:
        return tex

    base_token, _ = schematics_utils.resolve_token_for_render(raw_token)
    texture_key = next(
        (key for key in (raw_token, base_token, parsed.token) if key in textures),
        None,
    )
    if texture_key is None:
        return None

    tex = schematics_utils.get_texture_for_render(base_token, textures[texture_key].copy())
    if parsed.rotation:
        tex = utils.rotate_texture_by_degrees(tex, parsed.rotation)
    return tex


_CATALOG_FACE_SUFFIX: dict[OrbitFaceKind, str] = {
    "top": "top",
    "side": "side",
    "bottom": "bottom",
}


def _uses_orbit_catalog_cap(parsed) -> bool:
    """``minecraft:*`` palette tokens — orbit ±Y uses ``{block}_top.png``, not 2D bakes."""
    return parsed is not None and parsed.token == "minecraft" and bool(parsed.material)


def _resolve_orbit_catalog_block_face(
    raw_token: RawToken,
    entry: dict,
    face_kind: OrbitFaceKind,
):
    """Load ``{block}_{top|side|bottom}.png`` for catalog-backed registry tokens."""
    parsed = parse_structure_token(raw_token)
    if parsed is None:
        return None

    try:
        block_id = resolve_minecraft_block_id(entry, parsed)
    except Exception:
        block_id = None

    if not block_id and parsed.token == "minecraft" and parsed.material:
        block_id = f"minecraft:{parsed.material}"

    if not block_id or ":" not in block_id:
        return None

    block_name = block_id.split(":", 1)[1]
    suffix = _CATALOG_FACE_SUFFIX[face_kind]
    filename = f"{block_name}_{suffix}.png"
    texture_path = find_block_texture_path(BLOCK_TEXTURES_FOLDER, filename)

    if texture_path is not None:
        return _load_orbit_texture_file(filename)

    if face_kind != "top":
        return None

    catalog_parsed = parse_structure_token(block_id)
    if catalog_parsed is None:
        return None

    return load_catalog_texture_image(
        catalog_parsed,
        "top",
        constants.BLOCK_PX,
    )


def _token_with_side_facing(
    raw_token: RawToken,
    face_kind: OrbitFaceKind,
    side_facing: str | None,
) -> RawToken:
    if face_kind != "side" or not side_facing:
        return raw_token

    parsed = parse_structure_token(raw_token)
    if parsed is None:
        return raw_token

    return format_structure_token(replace(parsed, direction=side_facing))


def _resolve_bottom_texture(
    raw_token: RawToken,
    textures: MappedTextureImages,
    *,
    layer_cells: CellGrid | None,
    cell_x: int | None,
    cell_z: int | None,
):
    parsed = parse_structure_token(raw_token)
    if parsed is None:
        return None

    entry = get_block_entry(parsed) or {}
    render_textures = get_render_textures(entry)
    if "bottom" not in render_textures:
        return None

    bottom_token = format_structure_token(parsed)
    return schematics_utils.resolve_cell_texture(
        bottom_token,
        textures,
        view="top",
        layer_cells=layer_cells,
        cell_x=cell_x,
        cell_z=cell_z,
    )
