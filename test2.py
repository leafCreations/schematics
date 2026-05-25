import json
from pathlib import Path
from PIL import Image

ASSETS = Path("assets/")
BLOCK_W = 16
BLOCK_H = 16

# ---------------------------------------------------------
# Load model with parent resolution
# ---------------------------------------------------------
def load_model(path):
    with open(path, "r") as f:
        model = json.load(f)

    if "parent" not in model:
        return model

    parent_ref = model["parent"]

    if ":" not in parent_ref:
        parent_ref = "minecraft:" + parent_ref

    namespace, parent_path_str = parent_ref.split(":", 1)
    parent_path = ASSETS / "models" / (parent_path_str + ".json")

    parent = load_model(parent_path)

    textures = parent.get("textures", {}).copy()
    textures.update(model.get("textures", {}))

    elements = parent.get("elements", [])
    if "elements" in model:
        elements = model["elements"]

    return {
        "textures": textures,
        "elements": elements
    }

# ---------------------------------------------------------
# Texture loader
# ---------------------------------------------------------
def load_texture(ref, textures):
    if ref.startswith("#"):
        ref = textures[ref[1:]]

    if ":" not in ref:
        ref = "minecraft:" + ref

    namespace, path = ref.split(":", 1)
    tex_path = ASSETS / "textures" / (path + ".png")
    return Image.open(tex_path).convert("RGBA")

# ---------------------------------------------------------
# Rotate geometry around Y axis
# ---------------------------------------------------------
def rotate_element_coords(element, rotation):
    x1, y1, z1 = element["from"]
    x2, y2, z2 = element["to"]

    if rotation == 0:
        return x1, y1, z1, x2, y2, z2

    if rotation == 90:
        return (
            16 - z2, y1, x1,
            16 - z1, y2, x2
        )

    if rotation == 180:
        return (
            16 - x2, y1, 16 - z2,
            16 - x1, y2, 16 - z1
        )

    if rotation == 270:
        return (
            z1, y1, 16 - x2,
            z2, y2, 16 - x1
        )

# ---------------------------------------------------------
# Face visibility table
# ---------------------------------------------------------
VISIBLE_FACES = {
    "east":  ["east", "up", "down", "north", "south"],
    "west":  ["west", "up", "down", "north", "south"],
    "north": ["north", "up", "down", "east", "west"],
    "south": ["south", "up", "down", "east", "west"],
    "up":    ["up"],
    "down":  ["down"]
}

# ---------------------------------------------------------
# Render a model from a given direction
# ---------------------------------------------------------
def render_model(canvas, model, direction, rotation_offset=0):
    textures = model["textures"]
    elements = model["elements"]

    visible_faces = VISIBLE_FACES[direction]

    for element in elements:
        faces = element.get("faces", {})

        for face_name in visible_faces:
            if face_name not in faces:
                continue

            face = faces[face_name]
            tex = load_texture(face["texture"], textures)

            u1, v1, u2, v2 = face["uv"]
            crop = tex.crop((u1, v1, u2, v2))

            x1, y1, z1, x2, y2, z2 = rotate_element_coords(element, rotation_offset)

            if direction in ("east", "west"):
                width  = int(z2 - z1)
                height = int(y2 - y1)
                paste_x = int(z1)
                paste_y = BLOCK_H - int(y2)

            elif direction in ("north", "south"):
                width  = int(x2 - x1)
                height = int(y2 - y1)
                paste_x = int(x1)
                paste_y = BLOCK_H - int(y2)

            elif direction == "up":
                width  = int(x2 - x1)
                height = int(z2 - z1)
                paste_x = int(x1)
                paste_y = int(z1)

            elif direction == "down":
                width  = int(x2 - x1)
                height = int(z2 - z1)
                paste_x = int(x1)
                paste_y = int(z1)

            crop = crop.resize((width, height), Image.NEAREST)

            rotation = face.get("rotation", 0)
            if rotation != 0:
                crop = crop.rotate(-rotation, expand=True)

            canvas.alpha_composite(crop, (paste_x, paste_y))

# ---------------------------------------------------------
# MAIN — Universal renderer
# ---------------------------------------------------------
STAIR_SHAPE_MODELS = {
    "straight": "{base}",
    "outer_left": "{base}_outer",
    "outer_right": "{base}_outer",
}

STAIR_ROTATIONS = {
    "straight": {
        "north": 0,
        "east": 90,
        "south": 180,
        "west": 270,
    },
    "outer_right": {
        "north": 270,
        "east": 0,
        "south": 90,
        "west": 180,
    },
    "outer_left": {
        "north": 180,
        "east": 270,
        "south": 0,
        "west": 90,
    },
}

def resolve_stair_model_name(model_name, shape):
    if shape not in STAIR_SHAPE_MODELS:
        raise ValueError(f"Unsupported stair shape: {shape}")

    return STAIR_SHAPE_MODELS[shape].format(base=model_name)


def resolve_stair_rotation(shape, facing):
    if shape not in STAIR_ROTATIONS:
        raise ValueError(f"Unsupported stair shape: {shape}")

    if facing not in STAIR_ROTATIONS[shape]:
        raise ValueError(f"Unsupported stair facing: {facing}")

    return STAIR_ROTATIONS[shape][facing]


def render_block(
    model_name,
    direction="up",
    facing="north",
    shape="straight",
    rotation=None,
    output="output.png"
):
    canvas = Image.new("RGBA", (BLOCK_W, BLOCK_H), (0, 0, 0, 0))

    resolved_model_name = model_name
    resolved_rotation = rotation

    if model_name.endswith("_stairs"):
        resolved_model_name = resolve_stair_model_name(model_name, shape)

        if resolved_rotation is None:
            resolved_rotation = resolve_stair_rotation(shape, facing)

    if resolved_rotation is None:
        resolved_rotation = 0

    model = load_model(
        ASSETS / "models/block" / f"{resolved_model_name}.json"
    )

    render_model(
        canvas,
        model,
        direction,
        rotation_offset=resolved_rotation
    )

    canvas.save(output)
    print("Saved:", output)

# Example usage:
render_block(
    "oak_stairs",
    direction="down",
    facing="east",
    shape="outer_left",
    output="oak_stairs_outer_left_east.png"
)
