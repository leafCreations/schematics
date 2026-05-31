from __future__ import annotations

from helpers.sprite_baker.block_model import (
    block_model_path,
    has_block_model,
    render_block_model,
)


def fence_inventory_model_path(material: str):
    return block_model_path(f"{material}_fence_inventory")


def has_fence_inventory_model(material: str) -> bool:
    return has_block_model(f"{material}_fence_inventory")


def render_fence_inventory_model(
    material: str,
    size: int,
    *,
    direction: str = "down",
    rotation: int = 0,
):
    return render_block_model(
        f"{material}_fence_inventory",
        size,
        direction=direction,
        rotation=rotation,
    )
