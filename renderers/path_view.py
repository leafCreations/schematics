import random

import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from PIL import Image, ImageDraw

# Landscaping Rules
PATH_WIDTH = 3
TRIM_BLOCK = "g"
TRIM_WIDTH = 1
LIGHTING_SPACING = 7
LIGHTING_START_OFFSET = 10

INTERIOR_FILTER_LIST = ["B1", "B2", "T", "F", "X1", "X2"]

def _get_random_path_block():
    roll = random.random()
    if roll < 0.60: return "dp"
    elif roll < 0.75: return "g"
    elif roll < 0.90: return "d"
    elif roll < 0.97: return "C"
    else: return "M"

def generate_landscape_y_minus_1_cache(ctx: SchematicContext):
    grid = [["G" for _ in range(ctx.site_size)] for _ in range(ctx.site_size)]
    stair_global_center_x = ctx.offset_x + 4
    stair_global_bottom_z = ctx.offset_z + (ctx.struct_h - 1)
    path_start_z = stair_global_bottom_z + 1
    
    for z in range(path_start_z, ctx.site_size):
        path_left = stair_global_center_x - (PATH_WIDTH // 2)
        path_right = stair_global_center_x + (PATH_WIDTH // 2)
        trim_left = path_left - TRIM_WIDTH
        trim_right = path_right + TRIM_WIDTH
        for x in range(ctx.site_size):
            if path_left <= x <= path_right: grid[z][x] = _get_random_path_block()
            elif trim_left <= x <= trim_right: grid[z][x] = TRIM_BLOCK
    return grid

def generate_full_3d_landscape_cache(ctx: SchematicContext):
    site_map = {y: [["." for _ in range(ctx.site_size)] for _ in range(ctx.site_size)] for y in [-1, 0, 1]}
    y_minus_1 = generate_landscape_y_minus_1_cache(ctx)
    
    stair_global_center_x = ctx.offset_x + 4
    stair_global_bottom_z = ctx.offset_z + (ctx.struct_h - 1)
    path_start_z = stair_global_bottom_z + 1
    
    for z in range(ctx.site_size):
        for x in range(ctx.site_size): site_map[-1][z][x] = y_minus_1[z][x]
            
    for z in range(path_start_z, ctx.site_size):
        path_left = stair_global_center_x - (PATH_WIDTH // 2)
        path_right = stair_global_center_x + (PATH_WIDTH // 2)
        trim_left = path_left - TRIM_WIDTH
        trim_right = path_right + TRIM_WIDTH
        relative_z = z - path_start_z
        if relative_z >= LIGHTING_START_OFFSET and (relative_z - LIGHTING_START_OFFSET) % LIGHTING_SPACING == 0:
            if trim_left >= 0:
                site_map[0][z][trim_left] = "o"
                site_map[1][z][trim_left] = "i"
            if trim_right < ctx.site_size:
                site_map[0][z][trim_right] = "o"
                site_map[1][z][trim_right] = "i"

    for y in [0, 1]:
        for local_z in range(ctx.struct_h):
            tokens = ctx.data[y][local_z].split()
            global_z = ctx.offset_z + local_z
            for local_x in range(ctx.struct_w):
                global_x = ctx.offset_x + local_x
                t, _direction = schematics_utils.resolve_schematic_token(tokens[local_x])
                if t != "." and t not in INTERIOR_FILTER_LIST: site_map[y][global_z][global_x] = t
    return site_map

def render_path_focused_blueprint(ctx: SchematicContext):
    
    block_px = 30
    padding = 50
    panel_dim = ctx.site_size * block_px
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

    y_minus_1 = generate_landscape_y_minus_1_cache(ctx)

    for col_idx, layer_y in enumerate([-1, 0, 1]):
        sx = padding + col_idx * (panel_dim + padding)
        sy = top_margin

        draw.text(
            (sx, sy - 22),
            f"PROPERTY TOP-DOWN BLUEPRINT -> LAYER Y={layer_y}",
            fill=(40, 40, 40)
        )

        for z in range(ctx.site_size):
            for x in range(ctx.site_size):
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
                    lx = x - ctx.offset_x
                    lz = z - ctx.offset_z

                    if 0 <= lx < ctx.struct_w and 0 <= lz < ctx.struct_h:
                        token, _direction = schematics_utils.resolve_schematic_token(
                            ctx.data[0][lz].split()[lx]
                        )

                        if token not in INTERIOR_FILTER_LIST:
                            active_token = token

                    else:
                        rz = z - (ctx.offset_z + ctx.struct_h)

                        if (
                            rz >= LIGHTING_START_OFFSET
                            and (rz - LIGHTING_START_OFFSET) % LIGHTING_SPACING == 0
                        ):
                            if (
                                x == (ctx.offset_x + 4) - 2
                                or x == (ctx.offset_x + 4) + 2
                            ):
                                active_token = "o"

                    if active_token == ".":
                        active_token = base_token
                        is_ghost = True

                elif layer_y == 1:
                    lx = x - ctx.offset_x
                    lz = z - ctx.offset_z

                    if 0 <= lx < ctx.struct_w and 0 <= lz < ctx.struct_h:
                        token, _direction = schematics_utils.resolve_schematic_token(
                            ctx.data[1][lz].split()[lx]
                        )

                        if token not in INTERIOR_FILTER_LIST:
                            active_token = token

                    else:
                        rz = z - (ctx.offset_z + ctx.struct_h)

                        if (
                            rz >= LIGHTING_START_OFFSET
                            and (rz - LIGHTING_START_OFFSET) % LIGHTING_SPACING == 0
                        ):
                            if (
                                x == (ctx.offset_x + 4) - 2
                                or x == (ctx.offset_x + 4) + 2
                            ):
                                active_token = "i"

                    if active_token == ".":
                        active_token = base_token
                        is_ghost = True

                # Always draw the base ground color first.
                base_background_color = schematics_utils.get_background_color(
                    base_token,
                    default=(245, 245, 245)
                )

                draw.rectangle(
                    [bx, by, bx + block_px, by + block_px],
                    fill=base_background_color
                )

                # Then draw the active texture if one exists.
                if active_token in ctx.topdown_textures:
                    tex = schematics_utils.get_texture_for_render(active_token, ctx.topdown_textures[active_token])

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
                        fill=schematics_utils.get_background_color(
                            active_token,
                            default=base_background_color
                        )
                    )

                draw.rectangle(
                    [bx, by, bx + block_px, by + block_px],
                    outline=(40, 40, 40, 12 if is_ghost else 25)
                )


    img.save(ctx.output_dir / f"{ctx.name.lower().replace(' ', '_')}_site_topdown.png")
    
def render_site_elevations(ctx: SchematicContext):
    
    block_px=30
    padding=60
    cache = generate_full_3d_landscape_cache(ctx)

    panel_px_w = ctx.site_size * block_px
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
        for x in range(ctx.site_size):
            fn, fs = ".", "."

            for z in range(ctx.site_size):
                if cache[y][z][x] != ".":
                    fn = cache[y][z][x]
                    break

            for z in range(ctx.site_size - 1, -1, -1):
                if cache[y][z][x] != ".":
                    fs = cache[y][z][x]
                    break

            elevations["N"][y].append(fn)
            elevations["S"][y].append(fs)

        for z in range(ctx.site_size):
            fw, fe = ".", "."

            for x in range(ctx.site_size):
                if cache[y][z][x] != ".":
                    fw = cache[y][z][x]
                    break

            for x in range(ctx.site_size - 1, -1, -1):
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

            for col in range(ctx.site_size):
                token = tokens[col]

                bx = current_x + (col * block_px)
                by = current_y + (pixel_row * block_px)

                if token == ".":
                    background_color = (235, 245, 255)
                else:
                    background_color = schematics_utils.get_background_color(
                        token,
                        default=(235, 245, 255)
                    )

                draw.rectangle(
                    [bx, by, bx + block_px, by + block_px],
                    fill=background_color
                )

                if token in ctx.sideview_textures:
                    img.paste(
                        ctx.sideview_textures[token],
                        (bx, by),
                        ctx.sideview_textures[token] if ctx.sideview_textures[token].mode == "RGBA" else None
                    )

                elif token != ".":
                    fallback_color = schematics_utils.get_background_color(
                        token,
                        default=(230, 230, 230)
                    )

                    draw.rectangle(
                        [bx, by, bx + block_px, by + block_px],
                        fill=fallback_color
                    )

        current_x += panel_px_w + padding

    img.save(ctx.output_dir / f"{ctx.name.lower().replace(' ', '_')}_site_facades.png")