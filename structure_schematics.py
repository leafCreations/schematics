import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageChops

import helpers.utils as utils
from __init__ import ASSET_FOLDER, OUTPUT_SCHEMATICS_FOLDER, MAX_PANELS_PER_ROW, MAX_PANEL_ROWS_PER_IMAGE 

try:
    from registry import BLOCK_REGISTRY
except ImportError:
    # Allows this file to keep running while the registry is being migrated.
    BLOCK_REGISTRY = {}
    
BLOCK_REGISTRY = utils.load_block_registry("registry/blocks.yaml")

# --- STATIC GLOBAL MATRIX INITIALIZATION ---
random.seed(42)

# Global Environmental Scales

# Landscaping Rules
PATH_WIDTH = 3
TRIM_BLOCK = "g"
TRIM_WIDTH = 1
LIGHTING_SPACING = 7
LIGHTING_START_OFFSET = 10

# --- DATA REGISTRIES ---
INTERIOR_FILTER_LIST = ["B1", "B2", "T", "F", "X1", "X2"]


def resolve_registry_texture(entry, texture_type="top"):
    """Resolve a texture from registry data.

    Priority:
    1. schematic top_texture / side_texture override
    2. minecraft block-name fallback, e.g. minecraft:oak_planks -> oak_planks.png
    """
    schematic = entry.get("schematic", {})
    minecraft = entry.get("minecraft", {})
    explicit_key = f"{texture_type}_texture"

    if schematic.get(explicit_key):
        return schematic[explicit_key]

    block_id = minecraft.get("block")
    if not block_id:
        return None

    return utils.default_texture_name(block_id)


def build_registry_texture_mapping(texture_type="top"):
    mapping = {}

    for raw_token, entry in BLOCK_REGISTRY.items():
        schematic = entry.get("schematic", {})
        texture_name = resolve_registry_texture(entry, texture_type)

        if texture_name:
            mapping[raw_token] = texture_name

    return mapping



def build_registry_render_aliases():
    aliases = {}

    for raw_token, data in BLOCK_REGISTRY.items():
        schematic = data.get("schematic", {})
        direction = utils.normalize_direction(schematic.get("direction"))

        aliases[raw_token] = (raw_token, direction)

    return aliases


# --- TEXTURE MAPPINGS ---
# Legacy mappings stay as a safety net while BLOCK_REGISTRY is being migrated.
LEGACY_BASE_MAPPING = {        
    "l": "/custom/oak_slab.png",
    "dirt_path": "dirt_path_top.png", 
    "gravel": "gravel.png", 
    "dirt": "dirt.png",    
}

REGISTRY_TOP_TEXTURE_MAPPING = build_registry_texture_mapping("top")
REGISTRY_SIDE_TEXTURE_MAPPING = build_registry_texture_mapping("side")

TOP_DOWN_TEXTURE_MAPPING = {
    **LEGACY_BASE_MAPPING,
    "L": "oak_log_top.png",
    "l": "/custom/oak_slab_down.png",
    **REGISTRY_TOP_TEXTURE_MAPPING,
}

SIDE_VIEW_TEXTURE_MAPPING = {
    **LEGACY_BASE_MAPPING,
    "L": "oak_log.png",
    **REGISTRY_SIDE_TEXTURE_MAPPING,
}

REGISTRY_TOKEN_RENDER_ALIASES = build_registry_render_aliases()
BASE_MAPPING = LEGACY_BASE_MAPPING

def get_inventory_group(token):
    entry = BLOCK_REGISTRY.get(token, {})

    category = entry.get("category")
    if category:
        return category

    return get_display_name(token)


def collect_inventory_counts(raw_tokens):
    grouped_counts = Counter()
    group_icons = {}

    for token in raw_tokens:
        if token == ".":
            continue

        group_name = get_inventory_group(token)
        grouped_counts[group_name] += 1

        if group_name not in group_icons:
            group_icons[group_name] = token

    return grouped_counts, group_icons


def _material_sort_key(item):
    group_name, _count = item
    return group_name.lower()


def resolve_schematic_token(raw_token):
    """Return (base_token, direction) for schematic rendering/counting.

    Direction comes only from BLOCK_REGISTRY[token]["schematic"]["direction"].
    """

    token = raw_token.split("@")[0]

    if token == ".":
        return ".", None

    entry = BLOCK_REGISTRY.get(token)

    if entry:
        schematic = entry.get("schematic", {})
        direction = utils.normalize_direction(schematic.get("direction"))
        return token, direction

    return token, None

# Set this to True temporarily if you want each directional bed/chest cell
# to show its parsed direction letter. This is useful because some vanilla
# top-down bed/chest assets are nearly symmetrical after 180-degree rotation.
DRAW_DIRECTION_DEBUG_MARKERS = False

def rotate_directional_texture(texture, direction):
    """Rotate a square top-down asset so token direction is visible in schematics.

    Assumption: source assets are drawn in NORTH orientation by default.
    Uses lossless right-angle transpose operations instead of Image.rotate()
    so pixel-art textures do not get resampled or visually blurred.
    """
    if direction is None or direction == "N":
        return texture.copy()
    if direction == "E":
        return texture.transpose(Image.Transpose.ROTATE_270)
    if direction == "S":
        return texture.transpose(Image.Transpose.ROTATE_180)
    if direction == "W":
        return texture.transpose(Image.Transpose.ROTATE_90)
    return texture.copy()

def paste_schematic_token(img, textures, raw_token, xy, size=None, draw=None):
    """Paste a token texture using the raw token, not the stripped base token.

    Any schematic token with a parsed direction will rotate.
    Tokens without direction render in their default orientation.
    """
    base_token, direction = resolve_schematic_token(raw_token)

    if base_token not in textures:
        return False

    tex = textures[base_token]

    if size is not None and tex.size != (size, size):
        tex = tex.resize((size, size), resample=Image.Resampling.NEAREST)

    if direction is not None:
        tex = rotate_directional_texture(tex, direction)

    img.paste(
        tex,
        xy,
        tex if tex.mode == "RGBA" else None
    )

    if DRAW_DIRECTION_DEBUG_MARKERS and draw is not None and direction is not None:
        x, y = xy
        marker = direction or "?"
        draw.rectangle(
            [x, y, x + 10, y + 10],
            fill=(255, 255, 255),
            outline=(0, 0, 0)
        )
        draw.text((x + 2, y), marker, fill=(0, 0, 0))

    return True

# --- ENGINE UTILITY CALCULATION BLOCKS ---
def get_random_path_block():
    roll = random.random()
    if roll < 0.60: return "dp"
    elif roll < 0.75: return "g"
    elif roll < 0.90: return "d"
    elif roll < 0.97: return "C"
    else: return "M"

def generate_landscape_y_minus_1_cache():
    grid = [["G" for _ in range(SITE_SIZE)] for _ in range(SITE_SIZE)]
    stair_global_center_x = STRUCT_OFFSET_X + 4
    stair_global_bottom_z = STRUCT_OFFSET_Z + (STRUCT_H - 1)
    path_start_z = stair_global_bottom_z + 1
    
    for z in range(path_start_z, SITE_SIZE):
        path_left = stair_global_center_x - (PATH_WIDTH // 2)
        path_right = stair_global_center_x + (PATH_WIDTH // 2)
        trim_left = path_left - TRIM_WIDTH
        trim_right = path_right + TRIM_WIDTH
        for x in range(SITE_SIZE):
            if path_left <= x <= path_right: grid[z][x] = get_random_path_block()
            elif trim_left <= x <= trim_right: grid[z][x] = TRIM_BLOCK
    return grid

def generate_full_3d_landscape_cache():
    site_map = {y: [["." for _ in range(SITE_SIZE)] for _ in range(SITE_SIZE)] for y in [-1, 0, 1]}
    y_minus_1 = generate_landscape_y_minus_1_cache()
    
    stair_global_center_x = STRUCT_OFFSET_X + 4
    stair_global_bottom_z = STRUCT_OFFSET_Z + (STRUCT_H - 1)
    path_start_z = stair_global_bottom_z + 1
    
    for z in range(SITE_SIZE):
        for x in range(SITE_SIZE): site_map[-1][z][x] = y_minus_1[z][x]
            
    for z in range(path_start_z, SITE_SIZE):
        path_left = stair_global_center_x - (PATH_WIDTH // 2)
        path_right = stair_global_center_x + (PATH_WIDTH // 2)
        trim_left = path_left - TRIM_WIDTH
        trim_right = path_right + TRIM_WIDTH
        relative_z = z - path_start_z
        if relative_z >= LIGHTING_START_OFFSET and (relative_z - LIGHTING_START_OFFSET) % LIGHTING_SPACING == 0:
            if trim_left >= 0:
                site_map[0][z][trim_left] = "o"
                site_map[1][z][trim_left] = "i"
            if trim_right < SITE_SIZE:
                site_map[0][z][trim_right] = "o"
                site_map[1][z][trim_right] = "i"

    for y in [0, 1]:
        for local_z in range(STRUCT_H):
            tokens = STRUCTURE_DATA_3D[y][local_z].split()
            global_z = STRUCT_OFFSET_Z + local_z
            for local_x in range(STRUCT_W):
                global_x = STRUCT_OFFSET_X + local_x
                t, _direction = resolve_schematic_token(tokens[local_x])
                if t != "." and t not in INTERIOR_FILTER_LIST: site_map[y][global_z][global_x] = t
    return site_map

def compile_texture_set(texture_type, assets_dir, block_px):
    mapping = build_registry_texture_mapping(texture_type)
    loaded = {}

    for token, filename in mapping.items():
        for folder in [
            assets_dir,
            os.path.join(assets_dir, "block_assets"),
            os.path.join(assets_dir, "item_assets")
        ]:
            normalized_filename = filename.lstrip("/\\")
            path = os.path.join(folder, normalized_filename)

            if os.path.exists(path):
                img = (
                    Image.open(path)
                    .convert("RGBA")
                    .resize((block_px, block_px), Image.Resampling.NEAREST)
                )

                loaded[token] = img
                break

    return loaded

def render_legend(img, draw, textures, start_y, padding):

    legend_tokens = sorted(
        textures.keys(),
        key=lambda t: get_display_name(t).lower()
    )

    for idx, token in enumerate(legend_tokens):

        col, row = idx % 5, idx // 5

        kx = padding + col * 160
        ky = start_y + row * 30

        draw.rectangle(
            [kx, ky, kx + 20, ky + 20],
            outline="black"
        )

        if token in textures:
            img.paste(
                textures[token].resize((20, 20)),
                (kx, ky)
            )

        draw.text(
            (kx + 25, ky + 3),
            get_display_name(token),
            fill=(50, 50, 50)
        )

def collect_structure_material_counts():
    raw_tokens = []

    for _layer_y, rows in STRUCTURE_DATA_3D.items():
        for row in rows:
            for raw_token in row.split():
                token, _direction = resolve_schematic_token(raw_token)
                if token != ".":
                    raw_tokens.append(token)

    return collect_inventory_counts(raw_tokens)

def get_display_name(token):
    entry = BLOCK_REGISTRY.get(token)

    if entry:
        return entry.get("display_name", token)

    return token

def _material_sort_key(item):
    token, _count = item
    return get_display_name(token).lower()

def render_materials_inventory_blueprint(output_path, textures, project_name="Residence 1"):
    """Render a complete material inventory image grouped by registry category/display name."""

    raw_tokens = []

    for _layer_y, rows in STRUCTURE_DATA_3D.items():
        for row in rows:
            for raw_token in row.split():
                token, _direction = resolve_schematic_token(raw_token)
                if token != ".":
                    raw_tokens.append(token)

    material_counts, material_icons = collect_inventory_counts(raw_tokens)
    materials = sorted(material_counts.items(), key=_material_sort_key)

    row_h = 42
    header_h = 110
    footer_h = 35
    padding = 50
    img_w = 700
    img_h = max(360, header_h + (len(materials) * row_h) + footer_h)

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        font_header = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
        font_body = ImageFont.truetype("DejaVuSans.ttf", 15)
        font_count = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
    except Exception:
        font_title = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_count = ImageFont.load_default()

    draw.text((padding, 28), f"{project_name} - Complete Materials List", fill=(20, 20, 20), font=font_title)
    draw.text((padding, 74), "Image", fill=(80, 80, 80), font=font_header)
    draw.text((padding + 90, 74), "Material", fill=(80, 80, 80), font=font_header)
    draw.text((img_w - padding - 70, 74), "Count", fill=(80, 80, 80), font=font_header)
    draw.line([(padding, 98), (img_w - padding, 98)], fill=(210, 210, 210), width=2)

    y = header_h

    for idx, (group_name, count) in enumerate(materials):
        if idx % 2 == 0:
            draw.rectangle(
                [padding - 10, y - 6, img_w - padding + 10, y + row_h - 8],
                fill=(248, 248, 248)
            )

        icon_x = padding + 8
        icon_y = y
        icon_token = material_icons.get(group_name)

        if icon_token in textures:
            tex = textures[icon_token].resize((30, 30), resample=Image.Resampling.NEAREST)
            img.paste(tex, (icon_x, icon_y), tex if tex.mode == "RGBA" else None)

        else:
            draw.rectangle(
                [icon_x, icon_y, icon_x + 30, icon_y + 30],
                fill=get_background_color(icon_token, default=(230, 230, 230)),
                outline=(80, 80, 80)
            )        

        draw.text((padding + 90, y + 7), group_name, fill=(30, 30, 30), font=font_body)
        draw.text((img_w - padding - 45, y + 7), str(count), fill=(30, 30, 30), font=font_count)

        y += row_h

    draw.line(
        [(padding, img_h - footer_h), (img_w - padding, img_h - footer_h)],
        fill=(230, 230, 230),
        width=1
    )

    draw.text(
        (padding, img_h - 25),
        "Counts are grouped by registry category when present; otherwise by display name.",
        fill=(110, 110, 110),
        font=font_body
    )

    img.save(output_path)

# --- RENDERING METHODS ---
def render_structure_blueprint(output_path, textures, block_px=30, padding=40):
    """Render all structure layers using a canvas sized from the active stage config."""

    layer_ids = sorted(STRUCTURE_DATA_3D.keys())

    if not layer_ids:
        raise ValueError("STRUCTURE_DATA_3D has no layers to render.")

    columns = min(MAX_PANELS_PER_ROW, max(1, len(layer_ids)))
    rows = (len(layer_ids) + columns - 1) // columns

    panel_w = STRUCT_W * block_px
    panel_h = STRUCT_H * block_px

    header_h = 60
    layer_gap_y = 80
    legend_h = 150

    img_w = max(
        900,
        padding + (columns * panel_w) + ((columns + 1) * padding)
    )

    img_h = (
        header_h
        + (rows * panel_h)
        + (max(0, rows - 1) * layer_gap_y)
        + legend_h
        + padding
    )

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    for idx, layer in enumerate(layer_ids):
        col = idx % columns
        row = idx // columns

        sx = padding + col * (panel_w + padding)
        sy = header_h + row * (panel_h + layer_gap_y)

        draw.text(
            (sx, sy - 20),
            f"Layer Y={layer}",
            fill="black"
        )

        for z in range(STRUCT_H):
            tokens = STRUCTURE_DATA_3D[layer][z].split()

            for x in range(STRUCT_W):
                raw_token = tokens[x] if x < len(tokens) else "."
                token, _direction = resolve_schematic_token(raw_token)

                bx = sx + (x * block_px)
                by = sy + (z * block_px)

                if token == ".":
                    draw.rectangle(
                        [bx, by, bx + block_px, by + block_px],
                        fill=(245, 245, 245),
                        outline=(40, 40, 40, 20)
                    )

                elif token in textures:
                    draw.rectangle(
                        [bx, by, bx + block_px, by + block_px],
                        outline=(40, 40, 40, 20)
                    )

                    paste_schematic_token(
                        img,
                        textures,
                        raw_token,
                        (bx, by),
                        block_px,
                        draw
                    )

                else:
                    draw.rectangle(
                        [bx, by, bx + block_px, by + block_px],
                        fill=get_background_color(token, default=(245, 245, 245)),
                        outline=(40, 40, 40, 20)
                    )

                if token != ".":
                    draw.text(
                        (bx + 2, by + 2),
                        token,
                        fill="white",
                        stroke_width=1,
                        stroke_fill="black"
                    )

    legend_y = (
        header_h
        + (rows * panel_h)
        + (max(0, rows - 1) * layer_gap_y)
        + 35
    )

    render_legend(img, draw, textures, legend_y, padding)
    img.save(output_path)

# --- ENGINE METHOD 1: TOP-DOWN HOUSE MATRIX COMPOSER ---
from collections import Counter

def render_floor_blueprint(output_dir, floor_name, layers, textures, project_name, assets_directory):
    """Render scalable wrapped floor blueprints with automatic image pagination."""

    block_px = 30
    padding = 50
    layer_gap = 80
    top_margin = 120
    bottom_margin = 60
    inventory_w = 150

    panel_w = STRUCT_W * block_px
    panel_h = STRUCT_H * block_px
    layer_panel_w = panel_w + inventory_w

    columns = min(MAX_PANELS_PER_ROW, max(1, len(layers)))
    max_panels_per_image = columns * MAX_PANEL_ROWS_PER_IMAGE

    layer_pages = [
        layers[i:i + max_panels_per_image]
        for i in range(0, len(layers), max_panels_per_image)
    ]

    font_floor = ImageFont.load_default()
    font_layer = ImageFont.load_default()

    try:
        font_inventory = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
    except:
        font_inventory = ImageFont.load_default()

    for page_index, page_layers in enumerate(layer_pages, start=1):

        layer_count = len(page_layers)
        rows = (layer_count + columns - 1) // columns

        img_w = max(
            900,
            (padding * 2)
            + (columns * layer_panel_w)
            + (max(0, columns - 1) * layer_gap)
        )

        img_h = max(
            360,
            top_margin
            + (rows * panel_h)
            + (max(0, rows - 1) * layer_gap)
            + bottom_margin
        )

        img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        page_title = f"{project_name} - {floor_name}"

        if len(layer_pages) > 1:
            page_title += f" (Page {page_index}/{len(layer_pages)})"

        draw.text(
            (padding, 20),
            page_title,
            fill="black",
            font=font_floor
        )

        for i, layer in enumerate(page_layers):

            col = i % columns
            row = i // columns

            sx = padding + (col * (layer_panel_w + layer_gap))
            sy = top_margin + (row * (panel_h + layer_gap))

            draw.text(
                (sx, sy - 40),
                f"Layer Y={layer}",
                fill="black",
                font=font_layer
            )

            for x in range(STRUCT_W):
                draw.text(
                    (sx + (x * block_px) + 10, sy - 20),
                    str(x + 1),
                    fill="blue",
                    font=font_layer
                )

            for y in range(STRUCT_H):
                draw.text(
                    (sx - 20, sy + (y * block_px) + 5),
                    chr(65 + y),
                    fill="blue",
                    font=font_layer
                )

            panel_materials = []

            for z in range(STRUCT_H):

                tokens = STRUCTURE_DATA_3D[layer][z].split()

                for x in range(STRUCT_W):

                    raw_token = tokens[x] if x < len(tokens) else "."
                    token, _direction = resolve_schematic_token(raw_token)

                    bx = sx + (x * block_px)
                    by = sy + (z * block_px)

                    if token == ".":
                        draw.rectangle(
                            [bx, by, bx + block_px, by + block_px],
                            fill=(245, 245, 245),
                            outline=(230, 230, 230)
                        )

                    elif token in textures:
                        draw.rectangle(
                            [bx, by, bx + block_px, by + block_px],
                            outline=(230, 230, 230)
                        )

                        paste_schematic_token(
                            img,
                            textures,
                            raw_token,
                            (bx, by),
                            block_px,
                            draw
                        )

                        panel_materials.append(token)

                    else:
                        draw.rectangle(
                            [bx, by, bx + block_px, by + block_px],
                            fill=get_background_color(token, default=(245, 245, 245)),
                            outline=(230, 230, 230)
                        )

                        panel_materials.append(token)

            final_inventory, inventory_icons = collect_inventory_counts(panel_materials)

            lx = sx + panel_w + 20

            draw.rectangle(
                [lx, sy, lx + inventory_w - 10, sy + panel_h],
                fill="white"
            )

            for j, (group_name, count) in enumerate(
                sorted(final_inventory.items(), key=_material_sort_key)
            ):

                ly = sy + 20 + (j * 35)

                if ly + 30 > sy + panel_h:
                    draw.text(
                        (lx, ly),
                        "...",
                        fill="black",
                        font=font_inventory
                    )
                    break

                icon_token = inventory_icons.get(group_name)

                if icon_token in textures:

                    tex = textures[icon_token].resize(
                        (25, 25),
                        resample=Image.Resampling.NEAREST
                    )

                    img.paste(
                        tex,
                        (lx, ly),
                        tex if tex.mode == "RGBA" else None
                    )

                else:
                    draw.rectangle(
                        [lx, ly, lx + 25, ly + 25],
                        fill=get_background_color(icon_token, default=(230, 230, 230)),
                        outline=(80, 80, 80)
                    )

                draw.text(
                    (lx + 35, ly + 5),
                    f"x {count}",
                    fill="black",
                    font=font_inventory
                )

        page_suffix = ""

        if len(layer_pages) > 1:
            page_suffix = f"_part_{page_index}"

        output_path = os.path.join(
            output_dir,
            f"{floor_name.lower().replace(' ', '_')}{page_suffix}.png"
        )

        img.save(output_path)

# --- ENGINE METHOD 2: ISOLATED HOUSE SIDE ELEVATIONS RE-ROUTED ---
SIDE_VIEW_TORCH_BACKING_BY_VIEW = {
    "N": {"in"},
    "S": {"is"},
    "E": {"ie"},
    "W": {"iw"},
}

SIDE_VIEW_TORCH_TOKENS = {"in", "is", "ie", "iw", "it"}

def paste_side_view_token(img, textures, raw_token, xy, block_px, view_key=None):
    x, y = xy

    base_token, direction = resolve_schematic_token(raw_token)
    token = raw_token.split("@")[0]

    if token in SIDE_VIEW_TORCH_TOKENS:
        should_show_backing = token in SIDE_VIEW_TORCH_BACKING_BY_VIEW.get(view_key, set())

        if should_show_backing and "P" in textures:
            img.paste(
                textures["P"],
                (x, y),
                textures["P"] if textures["P"].mode == "RGBA" else None
            )

        if "i" in textures:
            torch_size = int(block_px * 0.60)
            offset = (block_px - torch_size) // 2
            torch_tex = textures["i"].resize(
                (torch_size, torch_size),
                resample=Image.Resampling.NEAREST
            )
            img.paste(
                torch_tex,
                (x + offset, y + offset),
                torch_tex if torch_tex.mode == "RGBA" else None
            )
        return True

    if base_token in textures:
        tex = textures[base_token]

        if tex.size != (block_px, block_px):
            tex = tex.resize(
                (block_px, block_px),
                resample=Image.Resampling.NEAREST
            )

        if direction is not None:
            tex = rotate_directional_texture(tex, direction)

        img.paste(
            tex,
            (x, y),
            tex if tex.mode == "RGBA" else None
        )
        return True

    return False

def render_structure_elevations(output_path, textures, block_px=30, padding=50):
    top_margin = 60
    panel_w = max(STRUCT_W, STRUCT_H) * block_px
    panel_h = 6 * block_px

    img_w = (panel_w * 4) + (padding * 5)
    img_h = top_margin + panel_h + 60

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.text(
        (padding, 20),
        "STRUCTURE SIDE-VIEW ELEVATIONS - ISOLATED BUILDING FAÇADES PROFILE",
        fill=(30, 30, 30)
    )

    struct_elevations = {
        k: {y: [] for y in range(6)}
        for k in ["N", "S", "W", "E"]
    }

    for y in range(6):
        for x in range(STRUCT_W):
            fn, fs = ".", "."

            for z in range(STRUCT_H):
                raw_token = STRUCTURE_DATA_3D[y][z].split()[x]
                token, _direction = resolve_schematic_token(raw_token)

                if token != ".":
                    fn = raw_token.split("@")[0]
                    break

            for z in range(STRUCT_H - 1, -1, -1):
                raw_token = STRUCTURE_DATA_3D[y][z].split()[x]
                token, _direction = resolve_schematic_token(raw_token)

                if token != ".":
                    fs = raw_token.split("@")[0]
                    break

            struct_elevations["N"][y].append(fn)
            struct_elevations["S"][y].append(fs)

        for z in range(STRUCT_H):
            fw, fe = ".", "."
            tokens = STRUCTURE_DATA_3D[y][z].split()

            for x in range(STRUCT_W):
                raw_token = tokens[x]
                token, _direction = resolve_schematic_token(raw_token)

                if token != ".":
                    fw = raw_token.split("@")[0]
                    break

            for x in range(STRUCT_W - 1, -1, -1):
                raw_token = tokens[x]
                token, _direction = resolve_schematic_token(raw_token)

                if token != ".":
                    fe = raw_token.split("@")[0]
                    break

            struct_elevations["W"][y].append(fw)
            struct_elevations["E"][y].append(fe)

    headings = [
        "NORTH FAÇADE (Rear)",
        "SOUTH FAÇADE (Front Door)",
        "WEST FAÇADE (Left Side)",
        "EAST FAÇADE (Right Side)"
    ]

    keys = ["N", "S", "W", "E"]
    current_x = padding
    current_y = top_margin + 20

    for idx, view_key in enumerate(keys):
        draw.text(
            (current_x, current_y - 20),
            headings[idx],
            fill=(60, 60, 60)
        )

        p_data = struct_elevations[view_key]
        tokens_count = STRUCT_W if view_key in ["N", "S"] else STRUCT_H

        for layer_y in range(6):
            pixel_row = 5 - layer_y
            tokens = p_data[layer_y]

            for col in range(tokens_count):
                raw_token = tokens[col] if col < len(tokens) else "."
                token, _direction = resolve_schematic_token(raw_token)

                bx = current_x + (col * block_px)
                by = current_y + (pixel_row * block_px)

                if token == ".":
                    draw.rectangle(
                        [bx, by, bx + block_px, by + block_px],
                        fill=(240, 248, 255)
                    )
                    continue

                rendered = paste_side_view_token(
                    img,
                    textures,
                    raw_token,
                    (bx, by),
                    block_px,
                    view_key
                )

                if not rendered:
                    draw.rectangle(
                        [bx, by, bx + block_px, by + block_px],
                        fill=get_background_color(token, default=(230, 230, 230))
                    )

        current_x += panel_w + padding

    img.save(output_path)

# --- ENGINE METHOD 3: TOP-DOWN PATHWAY PLOTS ---
def get_background_color(token, default=(245, 245, 245)):
    entry = BLOCK_REGISTRY.get(token, {})
    schematic = entry.get("schematic", {})

    background_color = schematic.get("background_color")

    if not background_color:
        return default

    if isinstance(background_color, str):
        hex_color = background_color.lstrip("#")

        if len(hex_color) == 6:
            return tuple(
                int(hex_color[i:i + 2], 16)
                for i in (0, 2, 4)
            )

    if isinstance(background_color, (list, tuple)) and len(background_color) == 3:
        return tuple(background_color)

    return default

def get_texture_for_render(token, texture):
    background_color = get_background_color(token, default=None)

    if background_color is None:
        return texture

    solid = Image.new(
        "RGBA",
        texture.size,
        tuple(background_color) + (255,)
    )

    return ImageChops.multiply(texture, solid)

def render_path_focused_blueprint(output_path, textures, block_px=30, padding=50):
    panel_dim = SITE_SIZE * block_px
    top_margin = 80
    img_w = (panel_dim * 3) + (padding * 4)
    img_h = top_margin + panel_dim + 80

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.text(
        (padding, 20),
        "LANDSCAPING SITE MAP PLANS - PATHWAY SECTORS & ALIGNMENT BUFFERS",
        fill=(30, 30, 30)
    )

    y_minus_1 = generate_landscape_y_minus_1_cache()

    for col_idx, layer_y in enumerate([-1, 0, 1]):
        sx = padding + col_idx * (panel_dim + padding)
        sy = top_margin

        draw.text(
            (sx, sy - 22),
            f"PROPERTY TOP-DOWN BLUEPRINT -> LAYER Y={layer_y}",
            fill=(40, 40, 40)
        )

        for z in range(SITE_SIZE):
            for x in range(SITE_SIZE):
                bx = sx + (x * block_px)
                by = sy + (z * block_px)

                base_token = y_minus_1[z][x]
                active_token = "."
                is_ghost = False
                is_ground_layer = False

                if layer_y == -1:
                    active_token = base_token
                    is_ground_layer = True

                elif layer_y == 0:
                    lx = x - STRUCT_OFFSET_X
                    lz = z - STRUCT_OFFSET_Z

                    if 0 <= lx < STRUCT_W and 0 <= lz < STRUCT_H:
                        token, _direction = resolve_schematic_token(
                            STRUCTURE_DATA_3D[0][lz].split()[lx]
                        )

                        if token not in INTERIOR_FILTER_LIST:
                            active_token = token

                    else:
                        rz = z - (STRUCT_OFFSET_Z + STRUCT_H)

                        if (
                            rz >= LIGHTING_START_OFFSET
                            and (rz - LIGHTING_START_OFFSET) % LIGHTING_SPACING == 0
                        ):
                            if (
                                x == (STRUCT_OFFSET_X + 4) - 2
                                or x == (STRUCT_OFFSET_X + 4) + 2
                            ):
                                active_token = "o"

                    if active_token == ".":
                        active_token = base_token
                        is_ghost = True

                elif layer_y == 1:
                    lx = x - STRUCT_OFFSET_X
                    lz = z - STRUCT_OFFSET_Z

                    if 0 <= lx < STRUCT_W and 0 <= lz < STRUCT_H:
                        token, _direction = resolve_schematic_token(
                            STRUCTURE_DATA_3D[1][lz].split()[lx]
                        )

                        if token not in INTERIOR_FILTER_LIST:
                            active_token = token

                    else:
                        rz = z - (STRUCT_OFFSET_Z + STRUCT_H)

                        if (
                            rz >= LIGHTING_START_OFFSET
                            and (rz - LIGHTING_START_OFFSET) % LIGHTING_SPACING == 0
                        ):
                            if (
                                x == (STRUCT_OFFSET_X + 4) - 2
                                or x == (STRUCT_OFFSET_X + 4) + 2
                            ):
                                active_token = "i"

                    if active_token == ".":
                        active_token = base_token
                        is_ghost = True

                # Always draw the base ground color first.
                base_background_color = get_background_color(
                    base_token,
                    default=(245, 245, 245)
                )

                draw.rectangle(
                    [bx, by, bx + block_px, by + block_px],
                    fill=base_background_color
                )

                # Then draw the active texture if one exists.
                if active_token in textures:
                    tex = get_texture_for_render(active_token, textures[active_token])

                    if is_ghost:
                        g_alpha = tex.split()[3].point(lambda p: int(p * 0.45))
                        img.paste(tex, (bx, by), g_alpha)
                    else:
                        img.paste(
                            tex,
                            (bx, by),
                            tex if tex.mode == "RGBA" else None
                        )

                # If no texture exists, draw the active token's background color.
                # Do NOT repaint the base terrain layer as a fallback.
                elif active_token != "." and not is_ground_layer:
                    draw.rectangle(
                        [bx, by, bx + block_px, by + block_px],
                        fill=get_background_color(
                            active_token,
                            default=base_background_color
                        )
                    )

                draw.rectangle(
                    [bx, by, bx + block_px, by + block_px],
                    outline=(40, 40, 40, 12 if is_ghost else 25)
                )

    img.save(output_path)

# --- ENGINE METHOD 4: MACRO SITE ELEVATIONS RE-ROUTED ---
def render_site_elevations(output_path, textures, block_px=30, padding=60):
    cache = generate_full_3d_landscape_cache()

    panel_px_w = SITE_SIZE * block_px
    top_margin = 80
    img_w = (panel_px_w * 4) + (padding * 5)
    img_h = top_margin + 50 + (3 * block_px) + 60

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.text(
        (padding, 20),
        "SITE CROSS-SECTIONS - 4 COMPASS DIRECTIONAL ENVIRONMENTAL PROJECTIONS",
        fill=(30, 30, 30)
    )

    elevations = {
        k: {y: [] for y in [-1, 0, 1]}
        for k in ["N", "S", "W", "E"]
    }

    for y in [-1, 0, 1]:
        for x in range(SITE_SIZE):
            fn, fs = ".", "."

            for z in range(SITE_SIZE):
                if cache[y][z][x] != ".":
                    fn = cache[y][z][x]
                    break

            for z in range(SITE_SIZE - 1, -1, -1):
                if cache[y][z][x] != ".":
                    fs = cache[y][z][x]
                    break

            elevations["N"][y].append(fn)
            elevations["S"][y].append(fs)

        for z in range(SITE_SIZE):
            fw, fe = ".", "."

            for x in range(SITE_SIZE):
                if cache[y][z][x] != ".":
                    fw = cache[y][z][x]
                    break

            for x in range(SITE_SIZE - 1, -1, -1):
                if cache[y][z][x] != ".":
                    fe = cache[y][z][x]
                    break

            elevations["W"][y].append(fw)
            elevations["E"][y].append(fe)

    headings = [
        "NORTH ELEVATION (Landscape View)",
        "SOUTH ELEVATION (Landscape View)",
        "WEST ELEVATION (Landscape View)",
        "EAST ELEVATION (Landscape View)"
    ]

    keys = ["N", "S", "W", "E"]
    current_x = padding
    current_y = top_margin + 50

    for idx, view_key in enumerate(keys):
        draw.text(
            (current_x, current_y - 22),
            headings[idx],
            fill=(60, 60, 60)
        )

        p_data = elevations[view_key]

        for step, layer_y in enumerate([-1, 0, 1]):
            pixel_row = 2 - step
            tokens = p_data[layer_y]

            for col in range(SITE_SIZE):
                token = tokens[col]

                bx = current_x + (col * block_px)
                by = current_y + (pixel_row * block_px)

                if token == ".":
                    background_color = (235, 245, 255)
                else:
                    background_color = get_background_color(
                        token,
                        default=(235, 245, 255)
                    )

                draw.rectangle(
                    [bx, by, bx + block_px, by + block_px],
                    fill=background_color
                )

                if token in textures:
                    img.paste(
                        textures[token],
                        (bx, by),
                        textures[token] if textures[token].mode == "RGBA" else None
                    )

                elif token != ".":
                    fallback_color = get_background_color(
                        token,
                        default=(230, 230, 230)
                    )

                    draw.rectangle(
                        [bx, by, bx + block_px, by + block_px],
                        fill=fallback_color
                    )

        current_x += panel_px_w + padding

    img.save(output_path)

# --- MASTER PIPELINE RUNNER WRAPPER ---
def build_stage_complete_schematics(structure="structure", stage=1):

    global STRUCTURE_DATA_3D
    global SITE_SIZE
    global STRUCT_W
    global STRUCT_H
    global STRUCT_OFFSET_X
    global STRUCT_OFFSET_Z

    config = utils.load_structure_config(structure, stage)

    STRUCTURE_DATA_3D = config["data"]
    SITE_SIZE = config["size"]
    STRUCT_W = config["struct_w"]
    STRUCT_H = config["struct_h"]
    STRUCT_OFFSET_X = config["offset_x"]
    STRUCT_OFFSET_Z = config["offset_z"]

    # 1. Define the specific sub-folder path   
    target_path = OUTPUT_SCHEMATICS_FOLDER / config["output_folder"]
    if not target_path.exists():
        target_path.mkdir(parents=True)
        print(f"[System Info] Created blueprint directory: {target_path}")
        
    # 2. Define the assets directory path
    assets_directory = ASSET_FOLDER / "textures/block"
    if not assets_directory.exists():
        raise FileNotFoundError(f"Assets directory not found: {assets_directory}")                
                
    print("\n" + "="*70)
    print("🤖 RUNNING AUTOMATED OMNI-BLUEPRINT COMPILE ENGINE...")
    print("="*70)        
    
    topdown_textures = compile_texture_set(
        "top",
        assets_directory,
        block_px=30
    )

    sideview_textures = compile_texture_set(
        "side",
        assets_directory,
        block_px=30
    )
    
    # 3. Generate Floor Plans in the NEW sub-folder    
    print("  ↳ Generation Node 1: Rendering floor-specific blueprint panels...")
    floor_map = config["floor_map"]
    for floor_name, layers in floor_map.items():
        # Pass 'target_path' instead of the root 'output_directory'
        render_floor_blueprint(target_path, floor_name, layers, topdown_textures, config["name"], assets_directory)
    
    # 4. Update the other Nodes to save into 'target_path' as well
    file_house_side = target_path / f"{config['name'].lower().replace(' ', '_')}_house_facades.png"
    render_structure_elevations(file_house_side, sideview_textures)
    
    file_path = target_path / f"{config['name'].lower().replace(' ', '_')}_site_topdown.png"
    render_path_focused_blueprint(file_path, topdown_textures)
    
    file_side = target_path / f"{config['name'].lower().replace(' ', '_')}_site_facades.png"
    render_site_elevations(file_side, sideview_textures)

    file_materials = target_path / f"{config['name'].lower().replace(' ', '_')}_materials_list.png"
    render_materials_inventory_blueprint(file_materials, topdown_textures, config["name"])
    
    print("="*70)
    print(f"🎉 ENGINE COMPLETE! Assets packed to: {target_path.resolve()}")
    print("="*70 + "\n")

if __name__ == "__main__":
    build_stage_complete_schematics(   
        structure="residence",     
        stage=2)
