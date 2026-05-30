import helpers.constants as constants
import helpers.fonts as font_utils
import helpers.materials as material_utils
import helpers.paths as paths
import helpers.render_image as render_image
from helpers.context import SchematicContext
from helpers.types import (
    MaterialsIconList,
    MaterialsLayout,
    MaterialsList,
)


def _build_material_layout(materials: MaterialsList) -> MaterialsLayout:
    row_h = 42
    header_h = 110
    footer_h = 35
    padding = constants.RENDER_PADDING
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


def _draw_material_header(
    draw,
    ctx: SchematicContext,
    layout: MaterialsLayout,
    fonts: font_utils.Fonts,
):
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
    fonts: font_utils.Fonts,
):
    y = layout["heading_h"]

    for idx, (group_name, count) in enumerate(materials_list):
        _draw_material_row_background(draw, idx, y, layout)

        icon_token = material_icons.get(group_name)

        material_utils.draw_inventory_icon(
            img,
            draw,
            ctx,
            icon_token,
            layout["padding"] + 8,
            y,
            size=30,
        )

        _draw_material_text(draw, group_name, count, y, layout, fonts)

        y += layout["row_h"]


def _draw_material_row_background(draw, idx: int, y: int, layout: MaterialsLayout):
    if idx % 2 != 0:
        return

    padding = layout["padding"]
    img_w = layout["img_w"]
    row_h = layout["row_h"]

    draw.rectangle([padding - 10, y - 6, img_w - padding + 10, y + row_h - 8], fill=(248, 248, 248))


def _draw_material_text(
    draw, group_name: str, count: int, y: int, layout: MaterialsLayout, fonts: font_utils.Fonts
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


def _draw_material_footer(draw, layout: MaterialsLayout, fonts: font_utils.Fonts):
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


def render_materials_inventory_blueprint(ctx: SchematicContext):
    parsed_tokens = material_utils.collect_material_tokens(ctx)

    materials, material_icons = material_utils.build_material_inventory(parsed_tokens, ctx)

    layout = _build_material_layout(materials)
    fonts = font_utils.load_materials_fonts()

    img, draw = render_image.create_canvas(layout["img_w"], layout["img_h"])

    _draw_material_header(draw, ctx, layout, fonts)

    _draw_material_rows(img, draw, ctx, materials, material_icons, layout, fonts)

    _draw_material_footer(draw, layout, fonts)

    output_path = paths.schematic_output_path(ctx, "materials_list.png")

    img.save(output_path)
