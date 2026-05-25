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
# Render EAST face of a model with rotation
# ---------------------------------------------------------
def render_east(canvas, model, rotation_offset=0):
    textures = model["textures"]
    elements = model["elements"]

    for element in elements:
        faces = element.get("faces", {})
        if "south" not in faces:
            continue

        face = faces["south"]
        tex = load_texture(face["texture"], textures)

        u1, v1, u2, v2 = face["uv"]
        crop = tex.crop((u1, v1, u2, v2))

        x1, y1, z1, x2, y2, z2 = rotate_element_coords(element, rotation_offset)

        width  = int(z2 - z1)
        height = int(y2 - y1)

        crop = crop.resize((width, height), Image.NEAREST)

        rotation = face.get("rotation", 0)
        if rotation != 0:
            crop = crop.rotate(-rotation, expand=True)

        paste_y = BLOCK_H - int(y2)
        canvas.alpha_composite(crop, (int(z1), paste_y))

# ---------------------------------------------------------
# MAIN — Render full oak fence (post + 4 rails)
# ---------------------------------------------------------
canvas = Image.new("RGBA", (BLOCK_W, BLOCK_H), (0, 0, 0, 0))

post_model = load_model(ASSETS / "models/block/oak_fence_post.json")
side_model = load_model(ASSETS / "models/block/oak_fence_side.json")

# Post
render_east(canvas, post_model, rotation_offset=0)

# Rails (all 4 directions)
render_east(canvas, side_model, rotation_offset=0)     # east
render_east(canvas, side_model, rotation_offset=90)    # south
render_east(canvas, side_model, rotation_offset=180)   # west
render_east(canvas, side_model, rotation_offset=270)   # north

canvas.save("oak_fence_south_view.png")
print("Saved oak_fence_south_view.png")
