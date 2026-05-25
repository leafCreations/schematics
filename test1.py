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
def render_block(model_name, direction="east", rotation=0, output="output.png"):
    canvas = Image.new("RGBA", (BLOCK_W, BLOCK_H), (0, 0, 0, 0))

    model = load_model(ASSETS / "models/block" / f"{model_name}.json")

    render_model(canvas, model, direction, rotation_offset=rotation)

    canvas.save(output)
    print("Saved:", output)

# Example usage:
render_block("oak_stairs", direction="north", rotation=0, output="oak_stairs_north.png")
