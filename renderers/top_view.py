import os

from __init__ import MAX_PANELS_PER_ROW, MAX_PANEL_ROWS_PER_IMAGE
from helpers.context import SchematicContext
import helpers.utils_schematics as schematics_utils

from PIL import Image, ImageDraw, ImageFont

# Public function to render floor blueprints
def render_floor_blueprints(ctx: SchematicContext):
    
    print("  ↳ Generation Node 1: Rendering floor-specific blueprint panels...")    
    for floor_name, layers in ctx.floor_map.items():
        _render_floor_blueprint(ctx, floor_name, layers)

def _render_floor_blueprint(ctx: SchematicContext, floor_name: str, layers: list):
    """Render scalable wrapped floor blueprints with automatic image pagination."""

    block_px = 30
    padding = 50
    layer_gap = 80
    top_margin = 120
    bottom_margin = 60
    inventory_w = 150

    panel_w = ctx.struct_w * block_px
    panel_h = ctx.struct_h * block_px
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

        page_title = f"{ctx.name} - {floor_name}"

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

            for x in range(ctx.struct_w):
                draw.text(
                    (sx + (x * block_px) + 10, sy - 20),
                    str(x + 1),
                    fill="blue",
                    font=font_layer
                )

            for y in range(ctx.struct_h):
                draw.text(
                    (sx - 20, sy + (y * block_px) + 5),
                    chr(65 + y),
                    fill="blue",
                    font=font_layer
                )

            panel_materials = []

            for z in range(ctx.struct_h):

                tokens = ctx.data[layer][z].split()

                for x in range(ctx.struct_w):

                    raw_token = tokens[x] if x < len(tokens) else "."
                    token, _direction = schematics_utils.resolve_schematic_token(raw_token)

                    bx = sx + (x * block_px)
                    by = sy + (z * block_px)

                    if token == ".":
                        draw.rectangle(
                            [bx, by, bx + block_px, by + block_px],
                            fill=(245, 245, 245),
                            outline=(230, 230, 230)
                        )

                    elif token in ctx.topdown_textures:
                        draw.rectangle(
                            [bx, by, bx + block_px, by + block_px],
                            outline=(230, 230, 230)
                        )

                        schematics_utils.paste_schematic_token(
                            img,
                            ctx.topdown_textures,
                            raw_token,
                            (bx, by),
                            block_px,
                            draw
                        )

                        panel_materials.append(token)

                    else:
                        draw.rectangle(
                            [bx, by, bx + block_px, by + block_px],
                            fill=schematics_utils.get_background_color(token, default=(245, 245, 245)),
                            outline=(230, 230, 230)
                        )

                        panel_materials.append(token)

            final_inventory, inventory_icons = schematics_utils.collect_inventory_counts(panel_materials)

            lx = sx + panel_w + 20

            draw.rectangle(
                [lx, sy, lx + inventory_w - 10, sy + panel_h],
                fill="white"
            )

            for j, (group_name, count) in enumerate(
                sorted(final_inventory.items(), key=schematics_utils.material_sort_key)
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

                if icon_token in ctx.topdown_textures:

                    tex = ctx.topdown_textures[icon_token].resize(
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
                        fill=schematics_utils.get_background_color(icon_token, default=(230, 230, 230)),
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
            ctx.output_dir,
            f"{floor_name.lower().replace(' ', '_')}{page_suffix}.png"
        )

        img.save(output_path)