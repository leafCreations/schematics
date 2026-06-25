"""Shared facing-block front texture resolution for 2D and 3D previews."""

from __future__ import annotations

import helpers.utils as utils
from helpers.block_texture_load import load_block_texture_image
from helpers.facing_block_state import resolve_facing_block_lit
from helpers.structure_tokens import parse_structure_token
from helpers.types import RawToken
from registries.loader import BLOCK_TEXTURES_FOLDER, find_block_texture_path, get_render_textures


def facing_block_front_texture_filename(raw_token: RawToken, entry: dict) -> str | None:
    render_textures = get_render_textures(entry)
    front = render_textures.get("top")
    if not isinstance(front, str):
        return None

    parsed = parse_structure_token(raw_token)
    if parsed is None:
        return front

    if resolve_facing_block_lit(parsed, entry):
        lit_name = front.replace(".png", "_on.png")
        if find_block_texture_path(BLOCK_TEXTURES_FOLDER, lit_name) is not None:
            return lit_name

    return front


def load_facing_block_front_texture(raw_token: RawToken, entry: dict, size: int):
    front_file = facing_block_front_texture_filename(raw_token, entry)
    if front_file is None:
        return None

    texture_path = find_block_texture_path(BLOCK_TEXTURES_FOLDER, front_file)
    if texture_path is None:
        return None

    tex = load_block_texture_image(texture_path, size)
    parsed = parse_structure_token(raw_token)
    if parsed is not None and parsed.rotation:
        tex = utils.rotate_texture_by_degrees(tex, parsed.rotation)
    return tex


def block_faces_facade(raw_token: RawToken, facade_direction: str) -> bool:
    """True when the block's ``@direction`` faces the facade viewer."""
    from helpers.utils_schematics import resolve_token_for_render

    _token, block_direction = resolve_token_for_render(raw_token)
    if block_direction is None:
        return False

    return utils.normalize_direction(block_direction) == facade_direction.upper()
