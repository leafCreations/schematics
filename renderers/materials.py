from helpers.context import SchematicContext
import helpers.utils_schematics as schematics_utils
from PIL import Image, ImageDraw, ImageFont
from helpers.types import MaterialsIconList, MaterialsList, RawTokenMaterialsList, Token, MaterialsLayout, Fonts

def _collect_material_tokens(ctx: SchematicContext) -> RawTokenMaterialsList:
    raw_tokens = []

    for _layer_y, rows in ctx.data.items():
        for row in rows:
            for raw_token in row.split():

                token, _direction = (
                    schematics_utils.resolve_schematic_token(raw_token)
                )

                if token != ".":
                    raw_tokens.append(token)

    return raw_tokens

def _build_material_layout(materials: RawTokenMaterialsList) -> MaterialsLayout:    

    row_h = 42
    header_h = 110
    footer_h = 35
    padding = 50
    img_w = 700

    img_h = max(
        360,
        header_h + (len(materials) * row_h) + footer_h
    )
    
    layout = MaterialsLayout(
        row_h=row_h,
        heading_h=header_h,
        footer_h=footer_h,
        padding=padding,
        img_w=img_w,
        img_h=img_h
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
        fonts["title"] = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            26
        )

        fonts["header"] = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            16
        )

        fonts["body"] = ImageFont.truetype(
            "DejaVuSans.ttf",
            15
        )

        fonts["count"] = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            15
        )

    except Exception:
        pass

    return fonts

def _create_material_image(layout: MaterialsLayout) -> tuple[Image.Image, ImageDraw.ImageDraw]:

    img = Image.new(
        "RGB",
        (layout["img_w"], layout["img_h"]),
        (255, 255, 255)
    )

    draw = ImageDraw.Draw(img)

    return img, draw

def _draw_material_header(
    draw,
    ctx: SchematicContext,
    layout: MaterialsLayout,
    fonts: Fonts
):

    padding = layout["padding"]
    img_w = layout["img_w"]

    draw.text(
        (padding, 28),
        f"{ctx.name} - Complete Materials List",
        fill=(20, 20, 20),
        font=fonts["title"]
    )

    draw.text(
        (padding, 74),
        "Image",
        fill=(80, 80, 80),
        font=fonts["header"]
    )

    draw.text(
        (padding + 90, 74),
        "Material",
        fill=(80, 80, 80),
        font=fonts["header"]
    )

    draw.text(
        (img_w - padding - 70, 74),
        "Count",
        fill=(80, 80, 80),
        font=fonts["header"]
    )

    draw.line(
        [(padding, 98), (img_w - padding, 98)],
        fill=(210, 210, 210),
        width=2
    )
    
def _draw_material_rows(
    img,
    draw,
    ctx: SchematicContext,
    materials_list: MaterialsList,
    material_icons: MaterialsIconList,
    layout: MaterialsLayout,
    fonts: Fonts
):

    y = layout["heading_h"]

    for idx, (group_name, count) in enumerate(materials_list):

        _draw_material_row_background(
            draw,
            idx,
            y,
            layout
        )

        icon_token = material_icons.get(group_name)

        _draw_material_icon(
            img,
            draw,
            ctx,
            icon_token,
            y,
            layout
        )

        _draw_material_text(
            draw,
            group_name,
            count,
            y,
            layout,
            fonts
        )

        y += layout["row_h"]
        
def _draw_material_row_background(
    draw,
    idx: int,
    y: int,
    layout: MaterialsLayout
):

    if idx % 2 != 0:
        return

    padding = layout["padding"]
    img_w = layout["img_w"]
    row_h = layout["row_h"]

    draw.rectangle(
        [
            padding - 10,
            y - 6,
            img_w - padding + 10,
            y + row_h - 8
        ],
        fill=(248, 248, 248)
    )
    
def _draw_material_icon(
    img,
    draw,
    ctx: SchematicContext,
    icon_token: Token,
    y: int,
    layout: MaterialsLayout
):

    padding = layout["padding"]

    icon_x = padding + 8
    icon_y = y

    if icon_token in ctx.topdown_textures:

        tex = ctx.topdown_textures[icon_token].resize(
            (30, 30),
            resample=Image.Resampling.NEAREST
        )

        img.paste(
            tex,
            (icon_x, icon_y),
            tex if tex.mode == "RGBA" else None
        )

        return

    draw.rectangle(
        [icon_x, icon_y, icon_x + 30, icon_y + 30],
        fill=schematics_utils.get_background_color(
            icon_token,
            default=(230, 230, 230)
        ),
        outline=(80, 80, 80)
    )
    
def _draw_material_text(
    draw,
    group_name: str,
    count: int,
    y: int,
    layout: MaterialsLayout,
    fonts: Fonts
):

    padding = layout["padding"]
    img_w = layout["img_w"]

    draw.text(
        (padding + 90, y + 7),
        group_name,
        fill=(30, 30, 30),
        font=fonts["body"]
    )

    draw.text(
        (img_w - padding - 45, y + 7),
        str(count),
        fill=(30, 30, 30),
        font=fonts["count"]
    )
    
def _draw_material_footer(
    draw,
    layout: MaterialsLayout,
    fonts: Fonts
):

    padding = layout["padding"]
    img_w = layout["img_w"]
    img_h = layout["img_h"]
    footer_h = layout["footer_h"]

    draw.line(
        [
            (padding, img_h - footer_h),
            (img_w - padding, img_h - footer_h)
        ],
        fill=(230, 230, 230),
        width=1
    )

    draw.text(
        (padding, img_h - 25),
        "Counts are grouped by registry category when present; otherwise by display name.",
        fill=(110, 110, 110),
        font=fonts["body"]
    )
    
def _build_material_output_path(ctx: SchematicContext) -> str:

    return (
        ctx.output_dir
        / f"{ctx.name.lower().replace(' ', '_')}_materials_list.png"
    )

def render_materials_inventory_blueprint(ctx: SchematicContext):

    raw_tokens = _collect_material_tokens(ctx)

    material_counts, material_icons = (
        schematics_utils.collect_inventory_counts(raw_tokens)
    )

    materials = sorted(
        material_counts.items(),
        key=schematics_utils.material_sort_key
    )

    layout = _build_material_layout(materials)
    fonts = _load_material_fonts()

    img, draw = _create_material_image(layout)

    _draw_material_header(draw, ctx, layout, fonts)

    _draw_material_rows(
        img,
        draw,
        ctx,
        materials,
        material_icons,
        layout,
        fonts
    )

    _draw_material_footer(draw, layout, fonts)

    output_path = _build_material_output_path(ctx)

    img.save(output_path)
    
    