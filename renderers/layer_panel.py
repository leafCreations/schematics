# renderers/layer_panel.py

import os
import helpers.utils_schematics as schematics_utils

from PIL import Image, ImageDraw, ImageFont
from helpers.context import SchematicContext

MAX_PANELS_PER_ROW = 3
MAX_PANEL_ROWS_PER_IMAGE = 3

def _build_layout(ctx, layers):
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

    return {
        "block_px": block_px,
        "padding": padding,
        "layer_gap": layer_gap,
        "top_margin": top_margin,
        "bottom_margin": bottom_margin,
        "inventory_w": inventory_w,
        "panel_w": panel_w,
        "panel_h": panel_h,
        "layer_panel_w": layer_panel_w,
        "columns": columns,
        "layer_pages": layer_pages,
    }
    
def _load_fonts():
    fonts = {
        "floor": ImageFont.load_default(),
        "layer": ImageFont.load_default(),
        "inventory": ImageFont.load_default(),
    }

    try:
        fonts["inventory"] = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
    except Exception:
        pass

    return fonts

def _draw_layer_panel(img, draw, ctx, layer, panel, fonts):
    sx = panel["sx"]
    sy = panel["sy"]
    block_px = panel["block_px"]

    _draw_layer_header(draw, layer, sx, sy, fonts)
    _draw_grid_labels(draw, ctx, sx, sy, block_px, fonts)

    panel_materials = []

    for z in range(ctx.struct_h):
        tokens = ctx.data[layer][z].split()

        for x in range(ctx.struct_w):
            raw_token = tokens[x] if x < len(tokens) else "."
            token, _direction = schematics_utils.resolve_schematic_token(raw_token)

            bx = sx + (x * block_px)
            by = sy + (z * block_px)

            _draw_block_cell(img, draw, ctx, raw_token, token, bx, by, block_px)

            if token != ".":
                panel_materials.append(token)

    return panel_materials

def _draw_block_cell(img, draw, ctx, raw_token, token, bx, by, block_px):
    rect = [bx, by, bx + block_px, by + block_px]

    if token == ".":
        draw.rectangle(rect, fill=(245, 245, 245), outline=(230, 230, 230))
        return

    if token in ctx.topdown_textures:
        draw.rectangle(rect, outline=(230, 230, 230))
        schematics_utils.paste_schematic_token(
            img,
            ctx.topdown_textures,
            raw_token,
            (bx, by),
            block_px,
            draw
        )
        return

    draw.rectangle(
        rect,
        fill=schematics_utils.get_background_color(token, default=(245, 245, 245)),
        outline=(230, 230, 230)
    )
    
def _create_page_image(layout: dict, page_layers: list):
    layer_count = len(page_layers)
    rows = (layer_count + layout["columns"] - 1) // layout["columns"]

    img_w = max(
        900,
        (layout["padding"] * 2)
        + (layout["columns"] * layout["layer_panel_w"])
        + (max(0, layout["columns"] - 1) * layout["layer_gap"])
    )

    img_h = max(
        360,
        layout["top_margin"]
        + (rows * layout["panel_h"])
        + (max(0, rows - 1) * layout["layer_gap"])
        + layout["bottom_margin"]
    )

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    return img, draw

def _draw_page_title(draw, ctx, floor_name, page_index, layout, fonts):
    page_title = f"{ctx.name} - {floor_name}"

    if len(layout["layer_pages"]) > 1:
        page_title += f" (Page {page_index}/{len(layout['layer_pages'])})"

    draw.text(
        (layout["padding"], 20),
        page_title,
        fill="black",
        font=fonts["floor"]
    )
    
def _get_panel_position(index: int, layout: dict):
    col = index % layout["columns"]
    row = index // layout["columns"]

    sx = layout["padding"] + (col * (layout["layer_panel_w"] + layout["layer_gap"]))
    sy = layout["top_margin"] + (row * (layout["panel_h"] + layout["layer_gap"]))

    return {
        "sx": sx,
        "sy": sy,
        "block_px": layout["block_px"],
        "panel_w": layout["panel_w"],
        "panel_h": layout["panel_h"],
        "inventory_w": layout["inventory_w"],
    }
    
def _draw_layer_header(draw, layer, sx, sy, fonts):
    draw.text(
        (sx, sy - 40),
        f"Layer Y={layer}",
        fill="black",
        font=fonts["layer"]
    )
    
def _draw_grid_labels(draw, ctx, sx, sy, block_px, fonts):
    for x in range(ctx.struct_w):
        draw.text(
            (sx + (x * block_px) + 10, sy - 20),
            str(x + 1),
            fill="blue",
            font=fonts["layer"]
        )

    for y in range(ctx.struct_h):
        draw.text(
            (sx - 20, sy + (y * block_px) + 5),
            chr(65 + y),
            fill="blue",
            font=fonts["layer"]
        )
        
def _draw_inventory_panel(img, draw, ctx, panel, panel_materials, fonts):
    final_inventory, inventory_icons = schematics_utils.collect_inventory_counts(panel_materials)

    lx = panel["sx"] + panel["panel_w"] + 20
    sy = panel["sy"]
    panel_h = panel["panel_h"]
    inventory_w = panel["inventory_w"]

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
                font=fonts["inventory"]
            )
            break

        icon_token = inventory_icons.get(group_name)

        _draw_inventory_icon(img, draw, ctx, icon_token, lx, ly)

        draw.text(
            (lx + 35, ly + 5),
            f"x {count}",
            fill="black",
            font=fonts["inventory"]
        )
        
def _draw_inventory_icon(img, draw, ctx, icon_token, lx, ly):
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
        return

    draw.rectangle(
        [lx, ly, lx + 25, ly + 25],
        fill=schematics_utils.get_background_color(
            icon_token,
            default=(230, 230, 230)
        ),
        outline=(80, 80, 80)
    )
    
def _build_output_path(ctx, floor_name, page_index, layout):
    page_suffix = ""

    if len(layout["layer_pages"]) > 1:
        page_suffix = f"_part_{page_index}"

    return os.path.join(
        ctx.output_dir,
        f"Structure_{floor_name.lower().replace(' ', '_')}{page_suffix}.png"
    )

def render_layer_blueprint(ctx: SchematicContext, floor_name: str, layers: list):
    layout = _build_layout(ctx, layers)
    fonts = _load_fonts()

    for page_index, page_layers in enumerate(layout["layer_pages"], start=1):
        img, draw = _create_page_image(layout, page_layers)
        _draw_page_title(draw, ctx, floor_name, page_index, layout, fonts)

        for i, layer in enumerate(page_layers):
            panel = _get_panel_position(i, layout)
            panel_materials = _draw_layer_panel(img, draw, ctx, layer, panel, fonts)
            _draw_inventory_panel(img, draw, ctx, panel, panel_materials, fonts)

        output_path = _build_output_path(ctx, floor_name, page_index, layout)
        img.save(output_path)