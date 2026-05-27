from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from helpers.context import SchematicContext
from helpers.structure_tokens import ParsedToken, parse_structure_token
from helpers.types import (
    Fonts,
    MaterialsIconList,
    MaterialsLayout,
    MaterialsList,
    ParsedTokenMaterialsList,
    RawTokenMaterialsList,
)


def _resolve_texture_path(ctx: SchematicContext, texture_name: str) -> Path:
    if texture_name.startswith("/custom/"):
        return ctx.assets_dir / "custom" / texture_name.removeprefix("/custom/")

    return ctx.assets_dir / texture_name


def _resolve_material_texture_name(parsed: ParsedToken, ctx: SchematicContext) -> str:
    entry = ctx.block_registry[parsed.token]
    defaults = entry.get("defaults", {})

    material = parsed.material or entry.get("material_default")
    variant = parsed.variant or defaults.get("variant")

    render = entry.get("render", {})
    textures = render.get("textures", {})

    inventory_image = render.get("inventory_image")

    if inventory_image:
        texture_name = inventory_image
    elif variant and variant in textures:
        texture_name = textures[variant]
    elif "top" in textures:
        texture_name = textures["top"]
    elif "side" in textures:
        texture_name = textures["side"]
    else:
        block_name = _resolve_material_block_name(parsed, ctx)
        texture_name = f"{block_name}.png"

    if material:
        texture_name = texture_name.format(material=material)

    return texture_name


def _collect_material_tokens(ctx: SchematicContext) -> ParsedTokenMaterialsList:
    parsed_tokens = []

    for layer in ctx.layers:
        for row in layer["cells"]:
            for raw_cell in row:
                parsed = parse_structure_token(raw_cell)

                if parsed is not None:
                    parsed_tokens.append(parsed)

    return parsed_tokens


def _format_material_name(block_name: str) -> str:
    return block_name.replace("_", " ").title()


def _resolve_material_block_name(parsed: ParsedToken, ctx: SchematicContext) -> str:
    entry = ctx.block_registry[parsed.token]
    defaults = entry.get("defaults", {})
    material = parsed.material or entry.get("material_default")
    variant = parsed.variant or defaults.get("variant")
    minecraft = entry["minecraft"]

    if "variants" in minecraft:
        if variant is None:
            raise ValueError(f"{parsed.token} requires a variant or defaults.variant")

        block_name = minecraft["variants"][variant]["block"]
    else:
        block_name = minecraft["block"]

    if material:
        block_name = block_name.format(material=material)

    return block_name.split(":", 1)[-1]


def _should_count_material(parsed: ParsedToken, ctx: SchematicContext) -> bool:
    entry = ctx.block_registry[parsed.token]
    behavior = entry["behavior"]

    if behavior == "door" and parsed.variant == "upper":
        return False

    return not (behavior == "bed" and parsed.variant == "foot")


def _build_material_inventory(
    parsed_tokens: ParsedTokenMaterialsList,
    ctx: SchematicContext,
) -> tuple[MaterialsList, MaterialsIconList]:
    material_counts = Counter()
    material_icons = {}

    for parsed in parsed_tokens:
        if not _should_count_material(parsed, ctx):
            continue

        block_name = _resolve_material_block_name(parsed, ctx)
        material_name = _format_material_name(block_name)

        material_counts[material_name] += 1
        material_icons.setdefault(material_name, _resolve_material_texture_name(parsed, ctx))

    materials = sorted(material_counts.items(), key=lambda item: item[0].lower())

    return materials, material_icons


def _build_material_layout(materials: RawTokenMaterialsList) -> MaterialsLayout:
    row_h = 42
    header_h = 110
    footer_h = 35
    padding = 50
    img_w = 700

    img_h = max(360, header_h + (len(materials) * row_h) + footer_h)

    layout = MaterialsLayout(
        row_h=row_h,
        heading_h=header_h,
        footer_h=footer_h,
        padding=padding,
        img_w=img_w,
        img_h=img_h,
    )

    return layout


def _load_material_fonts() -> Fonts:
    fonts = {
        "title": ImageFont.load_default(),
        "header": ImageFont.load_default(),
        "body": ImageFont.load_default(),
        "count": ImageFont.load_default(),
    }

    try:
        fonts["title"] = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)

        fonts["header"] = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)

        fonts["body"] = ImageFont.truetype("DejaVuSans.ttf", 15)

        fonts["count"] = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)

    except Exception:
        pass

    return fonts


def _create_material_image(
    layout: MaterialsLayout,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (layout["img_w"], layout["img_h"]), (255, 255, 255))

    draw = ImageDraw.Draw(img)

    return img, draw


def _draw_material_header(draw, ctx: SchematicContext, layout: MaterialsLayout, fonts: Fonts):
    padding = layout["padding"]
    img_w = layout["img_w"]

    draw.text(
        (padding, 28),
        f"{ctx.name} - Complete Materials List",
        fill=(20, 20, 20),
        font=fonts["title"],
    )

    draw.text((padding, 74), "Image", fill=(80, 80, 80), font=fonts["header"])

    draw.text((padding + 90, 74), "Material", fill=(80, 80, 80), font=fonts["header"])

    draw.text((img_w - padding - 70, 74), "Count", fill=(80, 80, 80), font=fonts["header"])

    draw.line([(padding, 98), (img_w - padding, 98)], fill=(210, 210, 210), width=2)


def _draw_material_rows(
    img,
    draw,
    ctx: SchematicContext,
    materials_list: MaterialsList,
    material_icons: MaterialsIconList,
    layout: MaterialsLayout,
    fonts: Fonts,
):
    y = layout["heading_h"]

    for idx, (group_name, count) in enumerate(materials_list):
        _draw_material_row_background(draw, idx, y, layout)

        icon_token = material_icons.get(group_name)

        _draw_material_icon(img, draw, ctx, icon_token, y, layout)

        _draw_material_text(draw, group_name, count, y, layout, fonts)

        y += layout["row_h"]


def _draw_material_row_background(draw, idx: int, y: int, layout: MaterialsLayout):
    if idx % 2 != 0:
        return

    padding = layout["padding"]
    img_w = layout["img_w"]
    row_h = layout["row_h"]

    draw.rectangle([padding - 10, y - 6, img_w - padding + 10, y + row_h - 8], fill=(248, 248, 248))


def _draw_material_icon(
    img,
    draw,
    ctx: SchematicContext,
    texture_name: str | None,
    y: int,
    layout: MaterialsLayout,
):
    padding = layout["padding"]
    icon_x = padding + 8
    icon_y = y

    if texture_name:
        texture_path = _resolve_texture_path(ctx, texture_name)

        if texture_path.exists():
            tex = Image.open(texture_path).convert("RGBA")
            tex = tex.resize((30, 30), resample=Image.Resampling.NEAREST)
            img.paste(tex, (icon_x, icon_y), tex)
            return

    draw.rectangle(
        [icon_x, icon_y, icon_x + 30, icon_y + 30],
        fill=(230, 230, 230),
        outline=(80, 80, 80),
    )


def _draw_material_text(
    draw, group_name: str, count: int, y: int, layout: MaterialsLayout, fonts: Fonts
):
    padding = layout["padding"]
    img_w = layout["img_w"]

    draw.text((padding + 90, y + 7), group_name, fill=(30, 30, 30), font=fonts["body"])

    draw.text(
        (img_w - padding - 45, y + 7),
        str(count),
        fill=(30, 30, 30),
        font=fonts["count"],
    )


def _draw_material_footer(draw, layout: MaterialsLayout, fonts: Fonts):
    padding = layout["padding"]
    img_w = layout["img_w"]
    img_h = layout["img_h"]
    footer_h = layout["footer_h"]

    draw.line(
        [(padding, img_h - footer_h), (img_w - padding, img_h - footer_h)],
        fill=(230, 230, 230),
        width=1,
    )

    draw.text(
        (padding, img_h - 25),
        "Counts are grouped by registry category when present; otherwise by display name.",
        fill=(110, 110, 110),
        font=fonts["body"],
    )


def _build_material_output_path(ctx: SchematicContext) -> str:
    return ctx.output_schematics_dir / f"{ctx.name.lower().replace(' ', '_')}_materials_list.png"


def render_materials_inventory_blueprint(ctx: SchematicContext):
    parsed_tokens = _collect_material_tokens(ctx)

    materials, material_icons = _build_material_inventory(parsed_tokens, ctx)

    layout = _build_material_layout(materials)
    fonts = _load_material_fonts()

    img, draw = _create_material_image(layout)

    _draw_material_header(draw, ctx, layout, fonts)

    _draw_material_rows(img, draw, ctx, materials, material_icons, layout, fonts)

    _draw_material_footer(draw, layout, fonts)

    output_path = _build_material_output_path(ctx)

    img.save(output_path)
