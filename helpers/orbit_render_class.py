"""Agent-facing orbit render-class taxonomy for 3D preview dispatch."""

from __future__ import annotations

from typing import Literal

from helpers.orbit_attachable_mesh import (
    is_attachable_behavior,
    is_block_model_face_behavior,
)
from helpers.orbit_partial_mesh import is_orbit_box_behavior
from helpers.registry_blocks import get_block_behavior
from helpers.registry_lookup import get_block_entry
from helpers.structure_tokens import parse_structure_token

OrbitRenderClass = Literal["solid_cube", "partial_box", "attachable_box", "block_model"]


def orbit_render_class(raw_token: str) -> OrbitRenderClass:
    """Classify a structure token for 3D orbit preview routing.

    Order: ``block_model`` → ``attachable_box`` → ``partial_box`` → ``solid_cube``.
    Thin wrapper over existing behavior helpers — no duplicate behavior lists.
    """
    if is_block_model_face_behavior(raw_token):
        return "block_model"

    parsed = parse_structure_token(raw_token)
    if parsed is not None:
        entry = get_block_entry(parsed) or {}
        behavior = get_block_behavior(entry)
        if is_attachable_behavior(behavior):
            return "attachable_box"

    if is_orbit_box_behavior(raw_token):
        return "partial_box"

    return "solid_cube"
