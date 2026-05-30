# renderers/layer_panel.py

import os
from collections import Counter
from contextlib import suppress

from PIL import Image, ImageDraw, ImageFont

import helpers.constants as constants
import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from helpers.structure_tokens import parse_structure_token
from helpers.types import (
    FloorBlueprintLayout,
    FloorBlueprintPanel,
    Fonts,
    Layers,
    RawToken,
    Token,
)
from renderers import materials

MAX_PANELS_PER_ROW = 3
MAX_PANEL_ROWS_PER_IMAGE = 3


def _build_layer_inventory(
    raw_tokens: list[RawToken],
    ctx: SchematicContext,
) -> tuple[list[tuple[str, int]], dict[str, str]]:
    inventory_counts = Counter()
    inventory_icons = {}

    for raw_token in raw_tokens:
        parsed = parse_structure_token(raw_token)

        if parsed is None or not materials._should_count_material(parsed, ctx):
            continue

        block_name = materials._resolve_material_block_name(parsed, ctx)
        group_name = materials._format_material_name(block_name)

        inventory_counts[group_name] += 1
        inventory_icons.setdefault(
            group_name, materials._resolve_material_texture_name(parsed, ctx)
        )

    return sorted(inventory_counts.items(), key=lambda item: item[0].lower()), inventory_icons


def _get_layer_width(layer: dict) -> int:
    return max((len(row) for row in layer.get("cells", [])), default=1)


def _get_layer_depth(layer: dict) -> int:
    return max(len(layer.get("cells", [])), 1)


def _build_layout(ctx: SchematicContext, layers: Layers) -> FloorBlueprintLayout:
    block_px = constants.BLOCK_PX
    padding = 50
    layer_gap = 80
    top_margin = 120
    bottom_margin = 60
    inventory_w = 150

    max_width = max((_get_layer_width(layer) for layer in layers), default=1)
    max_depth = max((_get_layer_depth(layer) for layer in layers), default=1)

    panel_w = max_width * block_px
    panel_h = max_depth * block_px
    layer_panel_w = panel_w + inventory_w

    columns = min(MAX_PANELS_PER_ROW, max(1, len(layers)))
    max_panels_per_image = columns * MAX_PANEL_ROWS_PER_IMAGE

    layer_pages = [
        layers[i : i + max_panels_per_image] for i in range(0, len(layers), max_panels_per_image)
    ]

    return FloorBlueprintLayout(
        block_px=block_px,
        padding=padding,
        layer_gap=layer_gap,
        top_margin=top_margin,
        bottom_margin=bottom_margin,
        inventory_w=inventory_w,
        panel_w=panel_w,
        panel_h=panel_h,
        layer_panel_w=layer_panel_w,
        columns=columns,
        layer_pages=layer_pages,
    )


def _load_fonts() -> Fonts:
    fonts = {
        "floor": ImageFont.load_default(),
        "layer": ImageFont.load_default(),
        "inventory": ImageFont.load_default(),
    }

    with suppress(OSError):
        fonts["inventory"] = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)

    return fonts


def _draw_layer_panel(
    img,
    draw,
    ctx: SchematicContext,
    layer: dict,
    panel: FloorBlueprintPanel,
    fonts: Fonts,
):
    sx = panel["sx"]
    sy = panel["sy"]
    block_px = panel["block_px"]

    layer_name = str(layer.get("name", "Layer"))
    layer_width = _get_layer_width(layer)
    layer_depth = _get_layer_depth(layer)

    _draw_layer_header(draw, layer_name, sx, sy, fonts)
    _draw_grid_labels(draw, sx, sy, block_px, layer_width, layer_depth, fonts)

    panel_materials = []

    for z, row in enumerate(layer.get("cells", [])):
        for x, raw_token in enumerate(row):
            token, _direction = schematics_utils.resolve_token_for_render(raw_token)

            bx = sx + (x * block_px)
            by = sy + (z * block_px)

            _draw_block_cell(img, draw, ctx, raw_token, token, bx, by, block_px)

            if token != ".":
                panel_materials.append(raw_token)

    return panel_materials


def _draw_block_cell(
    img,
    draw,
    ctx: SchematicContext,
    raw_token: RawToken,
    token: Token,
    bx: int,
    by: int,
    block_px: int,
):
    rect = [bx, by, bx + block_px, by + block_px]

    if token == ".":
        draw.rectangle(rect, fill=(245, 245, 245), outline=(230, 230, 230))
        return

    draw.rectangle(rect, outline=(230, 230, 230))

    if ctx.topdown_textures and schematics_utils.paste_topdown_token(
        img,
        ctx.topdown_textures,
        raw_token,
        (bx, by),
        block_px,
        draw,
    ):
        return

    draw.rectangle(
        rect,
        fill=schematics_utils.get_background_color(token, default=(245, 245, 245)),
        outline=(230, 230, 230),
    )


def _create_page_image(
    layout: FloorBlueprintLayout,
    page_layers: Layers,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    layer_count = len(page_layers)
    rows = (layer_count + layout["columns"] - 1) // layout["columns"]

    img_w = max(
        900,
        (layout["padding"] * 2)
        + (layout["columns"] * layout["layer_panel_w"])
        + (max(0, layout["columns"] - 1) * layout["layer_gap"]),
    )

    img_h = max(
        360,
        layout["top_margin"]
        + (rows * layout["panel_h"])
        + (max(0, rows - 1) * layout["layer_gap"])
        + layout["bottom_margin"],
    )

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    return img, draw


def _draw_page_title(
    draw,
    ctx: SchematicContext,
    floor_name: str,
    page_index: int,
    layout: FloorBlueprintLayout,
    fonts: Fonts,
):
    page_title = f"{ctx.name} - {floor_name}"

    if len(layout["layer_pages"]) > 1:
        page_title += f" (Page {page_index}/{len(layout['layer_pages'])})"

    draw.text((layout["padding"], 20), page_title, fill="black", font=fonts["floor"])


def _get_panel_position(index: int, layout: FloorBlueprintLayout) -> FloorBlueprintPanel:
    col = index % layout["columns"]
    row = index // layout["columns"]

    sx = layout["padding"] + (col * (layout["layer_panel_w"] + layout["layer_gap"]))
    sy = layout["top_margin"] + (row * (layout["panel_h"] + layout["layer_gap"]))

    return FloorBlueprintPanel(
        sx=sx,
        sy=sy,
        block_px=layout["block_px"],
        panel_w=layout["panel_w"],
        panel_h=layout["panel_h"],
        inventory_w=layout["inventory_w"],
    )


def _draw_layer_header(draw, layer_name: str, sx: int, sy: int, fonts: Fonts):
    draw.text((sx, sy - 40), layer_name, fill="black", font=fonts["layer"])


def _draw_grid_labels(
    draw,
    sx: int,
    sy: int,
    block_px: int,
    layer_width: int,
    layer_depth: int,
    fonts: Fonts,
):
    for x in range(layer_width):
        draw.text(
            (sx + (x * block_px) + 10, sy - 20),
            str(x + 1),
            fill="blue",
            font=fonts["layer"],
        )

    for z in range(layer_depth):
        draw.text(
            (sx - 20, sy + (z * block_px) + 5),
            chr(65 + z),
            fill="blue",
            font=fonts["layer"],
        )


def _draw_inventory_panel(
    img,
    draw,
    ctx: SchematicContext,
    panel: FloorBlueprintPanel,
    panel_materials: list[RawToken],
    fonts: Fonts,
):
    inventory, inventory_icons = _build_layer_inventory(panel_materials, ctx)

    lx = panel["sx"] + panel["panel_w"] + 20
    sy = panel["sy"]
    panel_h = panel["panel_h"]
    inventory_w = panel["inventory_w"]

    draw.rectangle([lx, sy, lx + inventory_w - 10, sy + panel_h], fill="white")

    for j, (group_name, count) in enumerate(inventory):
        ly = sy + 20 + (j * 35)

        if ly + 30 > sy + panel_h:
            draw.text((lx, ly), "...", fill="black", font=fonts["inventory"])
            break

        texture_name = inventory_icons.get(group_name)

        _draw_inventory_icon(img, draw, ctx, texture_name, lx, ly)

        draw.text((lx + 35, ly + 5), f"x {count}", fill="black", font=fonts["inventory"])


def _draw_inventory_icon(
    img,
    draw,
    ctx: SchematicContext,
    texture_name: str | None,
    lx: int,
    ly: int,
):
    if texture_name:
        texture_path = materials._resolve_texture_path(ctx, texture_name)

        if texture_path.exists():
            tex = Image.open(texture_path).convert("RGBA")
            tex = tex.resize((25, 25), resample=Image.Resampling.NEAREST)
            img.paste(tex, (lx, ly), tex)
            return

    draw.rectangle(
        [lx, ly, lx + 25, ly + 25],
        fill=(230, 230, 230),
        outline=(80, 80, 80),
    )


def _build_output_path(
    ctx: SchematicContext,
    floor_name: str,
    page_index: int,
    layout: FloorBlueprintLayout,
) -> str:
    page_suffix = ""

    if len(layout["layer_pages"]) > 1:
        page_suffix = f"_part_{page_index}"

    return os.path.join(
        ctx.output_schematics_dir,
        f"Structure_{floor_name.lower().replace(' ', '_')}{page_suffix}.png",
    )


def _draw_compass(draw, img_w: int, padding: int, fonts: Fonts):
    cx = img_w - padding - 45
    cy = 45
    size = 32

    draw.line((cx, cy - size, cx, cy + size), fill="black", width=2)
    draw.line((cx - size, cy, cx + size, cy), fill="black", width=2)

    draw.polygon(
        [
            (cx, cy - size - 10),
            (cx - 6, cy - size + 2),
            (cx + 6, cy - size + 2),
        ],
        fill="black",
    )

    draw.text((cx - 4, cy - size - 28), "N", fill="black", font=fonts["layer"])
    draw.text((cx - 4, cy + size + 8), "S", fill="black", font=fonts["layer"])
    draw.text((cx + size + 8, cy - 7), "E", fill="black", font=fonts["layer"])
    draw.text((cx - size - 18, cy - 7), "W", fill="black", font=fonts["layer"])


def render_layer_blueprint(ctx: SchematicContext, floor_name: str, layers: Layers):
    layout: FloorBlueprintLayout = _build_layout(ctx, layers)
    fonts: Fonts = _load_fonts()

    for page_index, page_layers in enumerate(layout["layer_pages"], start=1):
        img, draw = _create_page_image(layout, page_layers)
        _draw_page_title(draw, ctx, floor_name, page_index, layout, fonts)
        _draw_compass(draw, img.width, layout["padding"], fonts)

        for i, layer in enumerate(page_layers):
            panel: FloorBlueprintPanel = _get_panel_position(i, layout)
            panel_materials = _draw_layer_panel(img, draw, ctx, layer, panel, fonts)
            _draw_inventory_panel(img, draw, ctx, panel, panel_materials, fonts)

        output_path = _build_output_path(ctx, floor_name, page_index, layout)
        img.save(output_path)
