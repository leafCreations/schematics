from helpers.context import SchematicContext
import helpers.utils_schematics as schematics_utils
from PIL import Image, ImageDraw, ImageFont

def render_materials_inventory_blueprint(ctx: SchematicContext):
    """Render a complete material inventory image grouped by registry category/display name."""

    raw_tokens = []

    for _layer_y, rows in ctx.data.items():
        for row in rows:
            for raw_token in row.split():
                token, _direction =  schematics_utils.resolve_schematic_token(raw_token)
                if token != ".":
                    raw_tokens.append(token)

    material_counts, material_icons = schematics_utils.collect_inventory_counts(raw_tokens)
    materials = sorted(material_counts.items(), key=schematics_utils.material_sort_key)

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

    draw.text((padding, 28), f"{ctx.name} - Complete Materials List", fill=(20, 20, 20), font=font_title)
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

        if icon_token in ctx.topdown_textures:
            tex = ctx.topdown_textures[icon_token].resize((30, 30), resample=Image.Resampling.NEAREST)
            img.paste(tex, (icon_x, icon_y), tex if tex.mode == "RGBA" else None)

        else:
            draw.rectangle(
                [icon_x, icon_y, icon_x + 30, icon_y + 30],
                fill=schematics_utils.get_background_color(icon_token, default=(230, 230, 230)),
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

    img.save(ctx.output_dir / f"{ctx.name.lower().replace(' ', '_')}_materials_list.png")