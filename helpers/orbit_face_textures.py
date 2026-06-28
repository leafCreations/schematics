"""Face-aware catalog texture resolution for the 3D orbit preview."""

from __future__ import annotations

from dataclasses import replace
from typing import Literal

from PIL import Image

import helpers.constants as constants
import helpers.utils_schematics as schematics_utils
from helpers import utils
from helpers.block_texture_load import load_block_texture_image
from helpers.catalog_texture_exceptions import catalog_block_texture_name
from helpers.facing_block_textures import load_facing_block_front_texture
from helpers.registry_blocks import get_block_behavior, resolve_minecraft_block_id
from helpers.registry_lookup import (
    get_block_entry,
    is_minecraft_block_token,
    load_catalog_texture_image,
)
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

    behavior = get_block_behavior(entry)
    if behavior in {"bed", "chest"}:
        return _resolve_orbit_attachable_bake_face_texture(
            raw_token,
            textures,
            behavior=behavior,
            face_kind=face_kind,
            side_facing=side_facing,
            layer_cells=layer_cells,
            cell_x=cell_x,
            cell_z=cell_z,
            topdown_textures=topdown_textures,
            sideview_textures=sideview_textures,
        )

    if face_kind == "side":
        side_texture = _resolve_orbit_side_face_texture(
            raw_token,
            entry,
            parsed,
            textures,
            layer_cells=layer_cells,
            cell_x=cell_x,
            cell_z=cell_z,
            topdown_textures=topdown_textures,
            sideview_textures=sideview_textures,
            side_facing=side_facing,
        )
        if side_texture is not None:
            return side_texture

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


_ATTACHABLE_SIDE_ROLES = Literal["front", "back", "end"]
_OPPOSITE_COMPASS = {"N": "S", "S": "N", "E": "W", "W": "E"}
_COMPASS_ORDER = ("N", "E", "S", "W")


def _attachable_side_role(
    side_facing: str | None,
    block_facing: str | None,
) -> _ATTACHABLE_SIDE_ROLES | None:
    if not side_facing or not block_facing:
        return None

    compass = _SIDE_FACING_TO_COMPASS.get(side_facing.lower())
    if compass is None:
        return None
    if compass == block_facing:
        return "front"
    if compass == _OPPOSITE_COMPASS.get(block_facing):
        return "back"
    return "end"


def _end_cap_rotation_degrees(block_facing: str, end_compass: str) -> int:
    block_idx = _COMPASS_ORDER.index(block_facing)
    end_idx = _COMPASS_ORDER.index(end_compass)
    relative = (end_idx - block_idx) % 4
    if relative == 1:
        return 90
    if relative == 3:
        return 270
    return 0


def _resolve_chest_orbit_side_texture(
    raw_token: RawToken,
    textures: MappedTextureImages,
    *,
    face: Literal["front", "back", "end"],
    layer_cells: CellGrid | None,
    cell_x: int | None,
    cell_z: int | None,
):
    del textures, layer_cells, cell_x, cell_z

    parsed = parse_structure_token(raw_token)
    if parsed is None:
        return None

    entry = get_block_entry(parsed) or {}
    from helpers.sprite_baker.chest_schematic import compose_chest_side_schematic
    from helpers.sprite_baker.compose_chest import resolve_chest_part

    part = resolve_chest_part(parsed.variant, entry)
    return compose_chest_side_schematic(
        part=part,
        size=constants.BLOCK_PX,
        face=face,
    )


def _resolve_chest_orbit_top_texture(raw_token: RawToken):
    parsed = parse_structure_token(raw_token)
    if parsed is None:
        return None

    entry = get_block_entry(parsed) or {}
    from helpers.sprite_baker.chest_schematic import compose_chest_top_schematic
    from helpers.sprite_baker.compose_chest import resolve_chest_part

    part = resolve_chest_part(parsed.variant, entry)
    tex = compose_chest_top_schematic(part=part, size=constants.BLOCK_PX)
    _, resolved_direction = schematics_utils.resolve_token_for_render(raw_token)
    direction = parsed.direction or resolved_direction or entry.get("defaults", {}).get("direction")
    if direction:
        tex = utils.rotate_directional_texture(tex, direction)
    return tex


def _resolve_orbit_attachable_bake_face_texture(
    raw_token: RawToken,
    textures: MappedTextureImages,
    *,
    behavior: Literal["bed", "chest"],
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
        role = _attachable_side_role(side_facing, block_facing)
        side_map = _textures_for_view(
            "side",
            textures,
            topdown_textures,
            sideview_textures,
        )
        top_map = _textures_for_view(
            "top",
            textures,
            topdown_textures,
            sideview_textures,
        )

        if behavior == "chest":
            if role == "front":
                tex = _resolve_chest_orbit_side_texture(
                    raw_token,
                    side_map,
                    face="front",
                    layer_cells=layer_cells,
                    cell_x=cell_x,
                    cell_z=cell_z,
                )
            elif role == "back":
                tex = _resolve_chest_orbit_side_texture(
                    raw_token,
                    side_map,
                    face="back",
                    layer_cells=layer_cells,
                    cell_x=cell_x,
                    cell_z=cell_z,
                )
            else:
                tex = _resolve_chest_orbit_side_texture(
                    raw_token,
                    side_map,
                    face="end",
                    layer_cells=layer_cells,
                    cell_x=cell_x,
                    cell_z=cell_z,
                )
        elif role == "front":
            tex = schematics_utils.resolve_cell_texture(
                raw_token,
                side_map,
                view="side",
                layer_cells=layer_cells,
                cell_x=cell_x,
                cell_z=cell_z,
            )
        elif role == "back":
            tex = schematics_utils.resolve_cell_texture(
                raw_token,
                side_map,
                view="side",
                layer_cells=layer_cells,
                cell_x=cell_x,
                cell_z=cell_z,
            )
            if tex is not None:
                tex = tex.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif role == "end" and block_facing is not None:
            end_compass = _SIDE_FACING_TO_COMPASS.get(side_facing.lower())
            tex = schematics_utils.resolve_cell_texture(
                raw_token,
                top_map,
                view="top",
                layer_cells=layer_cells,
                cell_x=cell_x,
                cell_z=cell_z,
            )
            if tex is not None and end_compass is not None:
                degrees = _end_cap_rotation_degrees(block_facing, end_compass)
                if degrees:
                    tex = utils.rotate_texture_by_degrees(tex, degrees)
        else:
            tex = schematics_utils.resolve_cell_texture(
                raw_token,
                side_map,
                view="side",
                layer_cells=layer_cells,
                cell_x=cell_x,
                cell_z=cell_z,
            )

        return _force_opaque_orbit_face(tex)

    if behavior == "chest" and face_kind in {"top", "bottom"}:
        tex = _resolve_chest_orbit_top_texture(raw_token)
        return _force_opaque_orbit_face(tex)

    view: Literal["top", "side"] = "top" if face_kind in {"top", "bottom"} else "side"
    texture_map = _textures_for_view(
        view,
        textures,
        topdown_textures,
        sideview_textures,
    )
    tex = schematics_utils.resolve_cell_texture(
        raw_token,
        texture_map,
        view=view,
        layer_cells=layer_cells,
        cell_x=cell_x,
        cell_z=cell_z,
    )
    if tex is None:
        return None

    if behavior == "bed" and face_kind in {"top", "bottom"}:
        # Orbit +Y uses fract(world.z) for atlas v; schematic bakes place head/pillow on
        # the image top row (north in N-oriented assets). Flip so min-Z world edge
        # samples the pillow row after @direction rotation in resolve_cell_texture.
        tex = tex.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    return _force_opaque_orbit_face(tex)


def _force_opaque_orbit_face(image):
    """Solid orbit faces must not alpha-discard (e.g. dirt_path_side transparent rows)."""
    if image is None:
        return None

    rgba = image.convert("RGBA")
    red, green, blue, _alpha = rgba.split()
    opaque = Image.new("L", rgba.size, 255)
    return Image.merge("RGBA", (red, green, blue, opaque))


def _finalize_orbit_solid_face_texture(raw_token: RawToken, entry: dict, image):
    if image is None:
        return None

    behavior = get_block_behavior(entry)
    if behavior in {"fence", "wall"}:
        return image

    return _force_opaque_orbit_face(image)


def _resolve_orbit_side_face_texture(
    raw_token: RawToken,
    entry: dict,
    parsed,
    textures: MappedTextureImages,
    *,
    layer_cells: CellGrid | None,
    cell_x: int | None,
    cell_z: int | None,
    topdown_textures: MappedTextureImages | None,
    sideview_textures: MappedTextureImages | None,
    side_facing: str | None,
) -> Image.Image | None:
    """Side faces: prefer schematic/unified catalog (cobblestone path) before per-face PNGs."""
    token_for_resolve = _token_with_side_facing(raw_token, "side", side_facing)
    side_map = pick_textures_for_face_kind("side", topdown_textures, sideview_textures)
    if side_map is None:
        side_map = textures

    if parsed is not None and is_minecraft_block_token(parsed):
        baked = schematics_utils.resolve_cell_texture(
            token_for_resolve,
            side_map,
            view="side",
            layer_cells=layer_cells,
            cell_x=cell_x,
            cell_z=cell_z,
        )
        if baked is not None:
            return _finalize_orbit_solid_face_texture(raw_token, entry, baked)

        unified = load_catalog_texture_image(parsed, "side", constants.BLOCK_PX)
        if unified is not None:
            return _finalize_orbit_solid_face_texture(
                raw_token,
                entry,
                _apply_orbit_catalog_schematic_tint(raw_token, entry, unified),
            )

    catalog_side = _resolve_orbit_catalog_block_face(raw_token, entry, "side")
    if catalog_side is not None:
        return _finalize_orbit_solid_face_texture(raw_token, entry, catalog_side)

    return None


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


def _apply_orbit_catalog_schematic_tint(
    raw_token: RawToken,
    entry: dict,
    image,
):
    """Apply schematic tint (water/lava/grass) to a catalog block texture."""
    parsed = parse_structure_token(raw_token)
    block_id = None
    try:
        if parsed is not None:
            block_id = resolve_minecraft_block_id(entry, parsed)
    except Exception:
        block_id = None

    if not block_id and parsed is not None and parsed.token == "minecraft" and parsed.material:
        block_id = f"minecraft:{parsed.material}"

    if not block_id:
        return image

    return schematics_utils.get_texture_for_render(block_id, image.copy())


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
        image = _load_orbit_texture_file(filename)
        if image is None:
            return None
        return _apply_orbit_catalog_schematic_tint(raw_token, entry, image)

    fallback_name = catalog_block_texture_name(block_id)
    if fallback_name is not None:
        image = _load_orbit_texture_file(fallback_name)
        if image is not None:
            return _apply_orbit_catalog_schematic_tint(raw_token, entry, image)

    if face_kind != "top":
        return None

    catalog_parsed = parse_structure_token(block_id)
    if catalog_parsed is None:
        return None

    image = load_catalog_texture_image(
        catalog_parsed,
        "top",
        constants.BLOCK_PX,
    )
    if image is None:
        return None

    return _apply_orbit_catalog_schematic_tint(raw_token, entry, image)


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
