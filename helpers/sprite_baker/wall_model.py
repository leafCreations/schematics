from __future__ import annotations

from helpers.sprite_baker.block_model import (
    block_model_path,
    has_block_model,
    render_block_model,
)


def wall_inventory_model_path(material: str):
    return block_model_path(f"{material}_wall_inventory")


def has_wall_inventory_model(material: str) -> bool:
    return has_block_model(f"{material}_wall_inventory")


def render_wall_inventory_model(
    material: str,
    size: int,
    *,
    direction: str = "down",
    rotation: int = 0,
):
    return render_block_model(
        f"{material}_wall_inventory",
        size,
        direction=direction,
        rotation=rotation,
    )
