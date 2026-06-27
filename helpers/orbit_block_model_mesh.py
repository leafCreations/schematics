"""Block-model element faces for orbit preview attachables (torch, lantern, trapdoor)."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from helpers.orbit_mesh import OccupiedVoxel
from helpers.sprite_baker.block_model import (
    FACE_NORMALS,
    block_model_path,
    crop_model_face_texture,
    element_face_corners_in_block_space,
    has_block_model,
    load_block_model,
    rotate_block_space_y_normal,
)

_MODEL_SCALE = 1.0 / 16.0


@dataclass(frozen=True)
class BlockModelFaceQuad:
    normal: tuple[int, int, int]
    corners: tuple[tuple[float, float, float], ...]
    texture: Image.Image
    signature: str


def iter_block_model_face_quads(
    model_name: str,
    wx: float,
    wy: float,
    wz: float,
    *,
    rotation_y: int = 0,
) -> list[BlockModelFaceQuad]:
    """Emit axis-aligned element faces with per-face UV crops from a block model."""
    if not has_block_model(model_name):
        return []

    model = load_block_model(block_model_path(model_name))
    textures = model.get("textures", {})
    quads: list[BlockModelFaceQuad] = []

    for element_index, element in enumerate(model.get("elements", [])):
        faces = element.get("faces", {})
        for face_name, face in faces.items():
            base_normal = FACE_NORMALS.get(face_name)
            if base_normal is None:
                continue
            normal = rotate_block_space_y_normal(base_normal, rotation_y)

            local_corners = element_face_corners_in_block_space(
                element,
                face_name,
                rotation_y=rotation_y,
            )
            world_corners = tuple(
                (
                    wx + corner[0] * _MODEL_SCALE,
                    wy + corner[1] * _MODEL_SCALE,
                    wz + corner[2] * _MODEL_SCALE,
                )
                for corner in local_corners
            )
            texture = crop_model_face_texture(face, textures)
            u1, v1, u2, v2 = face["uv"]
            texture_ref = face.get("texture", "")
            signature = (
                f"bm:{model_name}:{rotation_y}:{element_index}:{face_name}:"
                f"{texture_ref}:{u1},{v1},{u2},{v2}"
            )
            quads.append(
                BlockModelFaceQuad(
                    normal=normal,
                    corners=world_corners,
                    texture=texture,
                    signature=signature,
                ),
            )

    return quads


def block_model_face_neighbor_occluded(
    cell: OccupiedVoxel,
    normal: tuple[int, int, int],
    voxel_map: dict[tuple[int, int, int], OccupiedVoxel],
) -> bool:
    """True when a solid neighbor blocks this outward-facing model face."""
    from helpers.orbit_partial_mesh import is_orbit_box_behavior

    neighbor = (
        cell.world[0] + normal[0],
        cell.world[1] + normal[1],
        cell.world[2] + normal[2],
    )
    neighbor_cell = voxel_map.get(neighbor)
    if neighbor_cell is None:
        return False
    return not is_orbit_box_behavior(neighbor_cell.token)
