from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image

from helpers.paths import ASSET_FOLDER

MODELS_DIR = ASSET_FOLDER / "models" / "block"
MODELS_ROOT = ASSET_FOLDER / "models"
TEXTURES_DIR = ASSET_FOLDER / "textures"
BLOCK_SIZE = 16

_VISIBLE_FACES = {
    "east": ["east", "up", "down", "north", "south"],
    "west": ["west", "up", "down", "north", "south"],
    "north": ["north", "up", "down", "east", "west"],
    "south": ["south", "up", "down", "east", "west"],
    "up": ["up"],
    "down": ["down"],
    # Top-down orthographic view (lantern cage + cap); chain added separately in compose_lantern.
    "hanging_top": ["up", "north", "south", "east", "west"],
}


def block_model_path(model_name: str) -> Path:
    return MODELS_DIR / f"{model_name}.json"


def has_block_model(model_name: str) -> bool:
    return block_model_path(model_name).exists()


def load_block_model(path: Path) -> dict:
    with path.open() as handle:
        model = json.load(handle)

    parent_ref = model.get("parent")
    if not parent_ref:
        return model

    if ":" not in parent_ref:
        parent_ref = f"minecraft:{parent_ref}"

    _namespace, parent_path_str = parent_ref.split(":", 1)
    parent_path = MODELS_ROOT / f"{parent_path_str}.json"
    parent = load_block_model(parent_path)

    textures = parent.get("textures", {}).copy()
    textures.update(model.get("textures", {}))

    elements = parent.get("elements", [])
    if "elements" in model:
        elements = model["elements"]

    return {"textures": textures, "elements": elements}


FACE_NORMALS: dict[str, tuple[int, int, int]] = {
    "down": (0, -1, 0),
    "up": (0, 1, 0),
    "north": (0, 0, -1),
    "south": (0, 0, 1),
    "east": (1, 0, 0),
    "west": (-1, 0, 0),
}


def load_block_model_texture(ref: str, textures: dict[str, str]) -> Image.Image:
    """Load a texture reference from a parsed block model."""
    return _load_texture(ref, textures)


def crop_model_face_texture(face: dict, textures: dict[str, str]) -> Image.Image:
    """Crop and orient the UV region for one block-model element face."""
    texture = _load_texture(face["texture"], textures)
    u1, v1, u2, v2 = face["uv"]
    left, right = sorted((u1, u2))
    top, bottom = sorted((v1, v2))
    crop = texture.crop((left, top, right, bottom))
    if u2 < u1:
        crop = crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if v2 < v1:
        crop = crop.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    face_rotation = face.get("rotation", 0)
    if face_rotation:
        crop = crop.rotate(-face_rotation, expand=True)

    return crop


_BLOCK_ROTATION_ORIGIN = (8.0, 8.0, 8.0)


def rotate_block_space_y(
    corner: tuple[float, float, float],
    degrees: int,
    *,
    origin: tuple[float, float, float] = _BLOCK_ROTATION_ORIGIN,
) -> tuple[float, float, float]:
    """Rotate a point in 0–16 block space around Y (Minecraft blockstate yaw)."""
    if degrees == 0:
        return corner

    x, y, z = corner
    ox, _, oz = origin
    radians = math.radians(degrees)
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)
    local_x = x - ox
    local_z = z - oz
    return (
        ox + local_x * cos_a - local_z * sin_a,
        y,
        oz + local_x * sin_a + local_z * cos_a,
    )


def rotate_block_space_y_normal(
    normal: tuple[int, int, int],
    degrees: int,
) -> tuple[int, int, int]:
    """Rotate a face normal with block Y rotation."""
    if degrees == 0:
        return normal

    x, y, z = float(normal[0]), float(normal[1]), float(normal[2])
    rotated = rotate_block_space_y((x, y, z), degrees, origin=(0.0, 0.0, 0.0))
    rx, ry, rz = rotated
    return (int(round(rx)), int(round(ry)), int(round(rz)))


def _element_box_corners_unrotated(
    element: dict,
) -> list[tuple[float, float, float]]:
    x1, y1, z1 = element["from"]
    x2, y2, z2 = element["to"]
    return [
        (x1, y1, z1),
        (x2, y1, z1),
        (x1, y2, z1),
        (x2, y2, z1),
        (x1, y1, z2),
        (x2, y1, z2),
        (x1, y2, z2),
        (x2, y2, z2),
    ]


def _transform_element_corners(
    element: dict,
    rotation_y: int,
) -> list[tuple[float, float, float]]:
    """Element rotation first, then block Y — matches Minecraft blockstate compose."""
    corners = _element_box_corners_unrotated(element)
    corners = [_apply_element_rotation(corner, element) for corner in corners]
    if rotation_y:
        corners = [rotate_block_space_y(corner, rotation_y) for corner in corners]
    return corners


def element_face_corners_in_block_space(
    element: dict,
    face_name: str,
    *,
    rotation_y: int = 0,
) -> tuple[tuple[float, float, float], ...]:
    """Return four oriented corners for one axis-aligned element face (0–16 space)."""
    x1, y1, z1 = element["from"]
    x2, y2, z2 = element["to"]
    min_x, max_x = sorted((x1, x2))
    min_y, max_y = sorted((y1, y2))
    min_z, max_z = sorted((z1, z2))

    if face_name == "up":
        raw = (
            (min_x, max_y, min_z),
            (min_x, max_y, max_z),
            (max_x, max_y, max_z),
            (max_x, max_y, min_z),
        )
    elif face_name == "down":
        raw = (
            (min_x, min_y, min_z),
            (max_x, min_y, min_z),
            (max_x, min_y, max_z),
            (min_x, min_y, max_z),
        )
    elif face_name == "east":
        raw = (
            (max_x, min_y, max_z),
            (max_x, max_y, max_z),
            (max_x, max_y, min_z),
            (max_x, min_y, min_z),
        )
    elif face_name == "west":
        raw = (
            (min_x, min_y, min_z),
            (min_x, min_y, max_z),
            (min_x, max_y, max_z),
            (min_x, max_y, min_z),
        )
    elif face_name == "south":
        raw = (
            (min_x, min_y, max_z),
            (max_x, min_y, max_z),
            (max_x, max_y, max_z),
            (min_x, max_y, max_z),
        )
    elif face_name == "north":
        raw = (
            (min_x, min_y, min_z),
            (min_x, max_y, min_z),
            (max_x, max_y, min_z),
            (max_x, min_y, min_z),
        )
    else:
        raise ValueError(f"Unknown block model face: {face_name}")

    transformed = [
        rotate_block_space_y(_apply_element_rotation(corner, element), rotation_y) for corner in raw
    ]
    return tuple(transformed)


def _load_texture(ref: str, textures: dict[str, str]) -> Image.Image:
    if ref.startswith("#"):
        ref = textures[ref[1:]]

    if ":" not in ref:
        ref = f"minecraft:{ref}"

    _namespace, path = ref.split(":", 1)
    texture_path = TEXTURES_DIR / f"{path}.png"
    return Image.open(texture_path).convert("RGBA")


def _rotate_element_coords(
    element: dict,
    rotation: int,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    x1, y1, z1 = element["from"]
    x2, y2, z2 = element["to"]

    if rotation == 0:
        return (x1, y1, z1), (x2, y2, z2)
    if rotation == 90:
        return (16 - z2, y1, x1), (16 - z1, y2, x2)
    if rotation == 180:
        return (16 - x2, y1, 16 - z2), (16 - x1, y2, 16 - z1)
    if rotation == 270:
        return (z1, y1, 16 - x2), (z2, y2, 16 - x1)

    raise ValueError(f"Unsupported block model rotation: {rotation}")


def _apply_element_rotation(
    corner: tuple[float, float, float],
    element: dict,
) -> tuple[float, float, float]:
    rotation = element.get("rotation")
    if not rotation:
        return corner

    origin = rotation["origin"]
    axis = rotation["axis"]
    angle = rotation["angle"]

    x, y, z = corner
    ox, oy, oz = origin

    if axis == "z":
        local_x = x - ox
        local_y = y - oy
        radians = math.radians(angle)
        cos_a = math.cos(radians)
        sin_a = math.sin(radians)
        rotated_x = ox + (local_x * cos_a - local_y * sin_a)
        rotated_y = oy + (local_x * sin_a + local_y * cos_a)
        return rotated_x, rotated_y, z

    if axis == "y":
        local_x = x - ox
        local_z = z - oz
        radians = math.radians(angle)
        cos_a = math.cos(radians)
        sin_a = math.sin(radians)
        rotated_x = ox + (local_x * cos_a - local_z * sin_a)
        rotated_z = oz + (local_x * sin_a + local_z * cos_a)
        return rotated_x, y, rotated_z

    return corner


def _element_bounds(
    element: dict, rotation_offset: int
) -> tuple[float, float, float, float, float, float]:
    (x1, y1, z1), (x2, y2, z2) = _rotate_element_coords(element, rotation_offset)
    corners = [
        _apply_element_rotation((x1, y1, z1), element),
        _apply_element_rotation((x2, y1, z1), element),
        _apply_element_rotation((x1, y2, z1), element),
        _apply_element_rotation((x2, y2, z1), element),
        _apply_element_rotation((x1, y1, z2), element),
        _apply_element_rotation((x2, y1, z2), element),
        _apply_element_rotation((x1, y2, z2), element),
        _apply_element_rotation((x2, y2, z2), element),
    ]

    xs = [corner[0] for corner in corners]
    ys = [corner[1] for corner in corners]
    zs = [corner[2] for corner in corners]
    return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)


def _render_model(
    canvas: Image.Image,
    model: dict,
    direction: str,
    *,
    rotation_offset: int = 0,
) -> None:
    textures = model["textures"]
    visible_faces = _VISIBLE_FACES[direction]

    for element in model["elements"]:
        faces = element.get("faces", {})
        x1, y1, z1, x2, y2, z2 = _element_bounds(element, rotation_offset)

        for face_name in visible_faces:
            if face_name not in faces:
                continue

            face = faces[face_name]
            texture = _load_texture(face["texture"], textures)
            u1, v1, u2, v2 = face["uv"]
            left, right = sorted((u1, u2))
            top, bottom = sorted((v1, v2))
            crop = texture.crop((left, top, right, bottom))
            if u2 < u1:
                crop = crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if v2 < v1:
                crop = crop.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

            if direction in {"east", "west"}:
                width = max(1, int(round(z2 - z1)))
                height = max(1, int(round(y2 - y1)))
                paste_x = int(round(z1))
                paste_y = BLOCK_SIZE - int(round(y2))
            elif direction in {"north", "south"}:
                width = max(1, int(round(x2 - x1)))
                height = max(1, int(round(y2 - y1)))
                paste_x = int(round(x1))
                paste_y = BLOCK_SIZE - int(round(y2))
            else:
                width = max(1, int(round(x2 - x1)))
                height = max(1, int(round(z2 - z1)))
                paste_x = int(round(x1))
                paste_y = int(round(z1))

            crop = crop.resize((width, height), Image.Resampling.NEAREST)

            face_rotation = face.get("rotation", 0)
            if face_rotation:
                crop = crop.rotate(-face_rotation, expand=True)

            canvas.alpha_composite(crop, (paste_x, paste_y))


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    """Return (min_x, min_y, max_x, max_y) for non-transparent pixels."""
    pixels = image.load()
    width, height = image.size
    min_x, min_y = width, height
    max_x = max_y = -1

    for y in range(height):
        for x in range(width):
            if pixels[x, y][3]:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if max_x < 0:
        return None

    return min_x, min_y, max_x, max_y


def render_block_model(
    model_name: str,
    size: int,
    *,
    direction: str = "down",
    rotation: int = 0,
) -> Image.Image:
    model_path = block_model_path(model_name)
    if not model_path.exists():
        raise FileNotFoundError(f"Block model not found: {model_path}")

    canvas = Image.new("RGBA", (BLOCK_SIZE, BLOCK_SIZE), (0, 0, 0, 0))
    model = load_block_model(model_path)
    _render_model(canvas, model, direction, rotation_offset=rotation)

    if canvas.size != (size, size):
        return canvas.resize((size, size), Image.Resampling.NEAREST)

    return canvas
