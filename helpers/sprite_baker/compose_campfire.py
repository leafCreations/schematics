from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.campfire_state import (
    CAMPFIRE_BLOCK_IDS,
    CAMPFIRE_FACINGS,
    is_campfire_block_id,
    resolve_campfire_facing,
    resolve_campfire_lit,
)
from helpers.registry_lookup import is_minecraft_block_token, minecraft_block_id
from helpers.sprite_baker.block_model import has_block_model, render_block_model
from helpers.sprite_baker.demo import SpriteBakeError
from helpers.structure_tokens import format_block_states, parse_structure_token
from helpers.types import TextureType

_FACING_ROTATION = {
    "south": 0,
    "west": 90,
    "north": 180,
    "east": 270,
}


def _campfire_model_name(block_id: str, *, lit: bool) -> str:
    if not lit:
        return "campfire_off"

    return block_id.split(":", 1)[-1]


def is_campfire_bake_key(key: str) -> bool:
    parsed = parse_structure_token(key)

    if parsed is None or not is_minecraft_block_token(parsed):
        return False

    return is_campfire_block_id(minecraft_block_id(parsed))


def _campfire_bake_key(block_id: str, *, facing: str, lit: bool) -> str:
    states = format_block_states((("lit", lit),))
    return f"{block_id}@{facing};{states}"


def list_campfire_bake_keys(view: TextureType = "top") -> list[str]:
    del view

    from helpers.block_picker import catalog_block_ids, resolve_palette

    palette = resolve_palette("lighting")

    if palette is None:
        block_ids = sorted(CAMPFIRE_BLOCK_IDS)
    else:
        block_ids: list[str] = []

        for entry in palette.entries:
            if not entry.is_catalog_block:
                continue

            ids = catalog_block_ids(entry) & CAMPFIRE_BLOCK_IDS

            if ids:
                block_ids.extend(sorted(ids))

        block_ids = sorted(dict.fromkeys(block_ids))

    keys: list[str] = []

    for block_id in block_ids:
        for facing in CAMPFIRE_FACINGS:
            for lit in (True, False):
                keys.append(_campfire_bake_key(block_id, facing=facing, lit=lit))

    return keys


def compose_campfire(
    *,
    key: str,
    view: TextureType | str,
    size: int,
    textures_dir: Path,
) -> Image.Image:
    del textures_dir

    parsed = parse_structure_token(key)

    if parsed is None or not is_minecraft_block_token(parsed):
        raise SpriteBakeError(f"Invalid campfire bake key: {key}")

    block_id = minecraft_block_id(parsed)

    if not is_campfire_block_id(block_id):
        raise SpriteBakeError(f"Not a campfire block id: {key}")

    facing = resolve_campfire_facing(parsed)
    lit = resolve_campfire_lit(parsed)

    model_name = _campfire_model_name(block_id, lit=lit)

    if not has_block_model(model_name):
        raise SpriteBakeError(f"Campfire model not found: {model_name}")

    direction = "down" if view == "top" else "east"
    rotation = _FACING_ROTATION.get(facing, 0)
    return render_block_model(model_name, size, direction=direction, rotation=rotation)


def compose_campfire_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    **_kwargs,
) -> Image.Image:
    return compose_campfire(key=key, view=view, size=size, textures_dir=textures_dir)
