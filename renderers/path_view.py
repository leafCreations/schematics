import helpers.utils_schematics as schematics_utils
import helpers.landscape_utils as landscape_utils
from helpers.context import SchematicContext
from PIL import Image, ImageDraw
from helpers.types import PathLayout, PathPanel, RawToken, SiteLayer, Token, BackgroundColor, Layers,  Cell

def _build_path_layout(ctx: SchematicContext) -> PathLayout:
    block_px = 30
    padding = 50
    top_margin = 80
    layers = [-1, 0, 1]

    panel_dim = ctx.site_size * block_px

    img_w = (panel_dim * len(layers)) + (padding * (len(layers) + 1))
    img_h = top_margin + panel_dim + 80
    
    layout = PathLayout(
        block_px=block_px,
        padding=padding,
        top_margin=top_margin,
        layers=layers,
        panel_dim=panel_dim,
        img_w=img_w,
        img_h=img_h
    )

    return layout

def _create_path_image(layout: PathLayout) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new(
        "RGB",
        (layout["img_w"], layout["img_h"]),
        (255, 255, 255)
    )

    draw = ImageDraw.Draw(img)

    return img, draw

def _draw_path_layer_header(draw, layer_y: int, panel: PathPanel):
    draw.text(
        (panel["sx"], panel["sy"] - 22),
        f"PROPERTY TOP-DOWN BLUEPRINT -> LAYER Y={layer_y}",
        fill=(40, 40, 40)
    )
    
def _draw_path_title(draw, layout: PathLayout):
    draw.text(
        (layout["padding"], 20),
        "LANDSCAPING SITE MAP PLANS - PATHWAY SECTORS & ALIGNMENT BUFFERS",
        fill=(30, 30, 30)
    )

def _get_path_panel_position(col_idx: int, layout: PathLayout) -> PathPanel:
    sx = layout["padding"] + col_idx * (
        layout["panel_dim"] + layout["padding"]
    )

    sy = layout["top_margin"]

    return {
        "sx": sx,
        "sy": sy,
    }
    
def _draw_path_layer_panel(
    img,
    draw,
    ctx: SchematicContext,
    layer_y: int,
    panel: PathPanel,
    layout: PathLayout,
    siteLayer: SiteLayer
):
    for z in range(ctx.site_size):
        for x in range(ctx.site_size):
            cell = _resolve_path_cell(ctx, layer_y, x, z, siteLayer)
            _draw_path_cell(img, draw, ctx, cell, x, z, panel, layout)
            
def _resolve_path_cell(
    ctx: SchematicContext,
    layer_y: int,
    x: int,
    z: int,
    siteLayer: SiteLayer
) -> Cell:
    base_token = siteLayer[z][x]
    
    cell = Cell(
        base_token=base_token,
        active_token=".",
        is_ghost=False,
        is_ground_layer=False,
    )    

    if layer_y == -1:
        cell["active_token"] = base_token
        cell["is_ground_layer"] = True
        return cell

    structure_token = _get_structure_overlay_token(ctx, layer_y, x, z)

    if structure_token != ".":
        cell["active_token"] = structure_token
        return cell

    lighting_token = _get_lighting_overlay_token(ctx, layer_y, x, z)

    if lighting_token != ".":
        cell["active_token"] = lighting_token
        return cell

    cell["active_token"] = base_token
    cell["is_ghost"] = True

    return cell

def _get_structure_overlay_token(
    ctx: SchematicContext,
    layer_y: int,
    x: int,
    z: int
) -> Token:
    lx = x - ctx.offset_x
    lz = z - ctx.offset_z

    if not _is_inside_structure(ctx, lx, lz):
        return "."

    raw_token = _get_structure_raw_token(ctx, layer_y, lx, lz)
    token, _direction = schematics_utils.resolve_schematic_token(raw_token)

    if not schematics_utils.show_interior_view(token):
        return "."

    return token

def _is_inside_structure(ctx: SchematicContext, lx: int, lz: int) -> bool:
    return (
        0 <= lx < ctx.struct_w
        and 0 <= lz < ctx.struct_h
    )
    
def _get_structure_raw_token(
    ctx: SchematicContext,
    layer_y: int,
    lx: int,
    lz: int
) -> RawToken:
    if layer_y not in ctx.data:
        return "."

    if lz >= len(ctx.data[layer_y]):
        return "."

    tokens = ctx.data[layer_y][lz].split()

    if lx >= len(tokens):
        return "."

    return tokens[lx]

def _get_lighting_overlay_token(
    ctx: SchematicContext,
    layer_y: int,
    x: int,
    z: int
) -> Token:
    if layer_y == 0:
        lighting_token = "o"
    elif layer_y == 1:
        lighting_token = "i"
    else:
        return "."

    if not _is_lighting_row(ctx, z):
        return "."

    if not _is_lighting_column(ctx, x):
        return "."

    return lighting_token

def _is_lighting_row(ctx: SchematicContext, z: int) -> bool:
    relative_z = z - (ctx.offset_z + ctx.struct_h)

    return (
        relative_z >= landscape_utils.LIGHTING_START_OFFSET
        and (
            relative_z - landscape_utils.LIGHTING_START_OFFSET
        ) % landscape_utils.LIGHTING_SPACING == 0
    )
    
def _is_lighting_column(ctx: SchematicContext, x: int) -> bool:
    stair_center_x = ctx.offset_x + 4

    return (
        x == stair_center_x - 2
        or x == stair_center_x + 2
    )
    
def _draw_path_cell(
    img,
    draw,
    ctx: SchematicContext,
    cell: Cell,
    x: int,
    z: int,
    panel: PathPanel,
    layout: PathLayout
):
    block_px = layout["block_px"]

    bx = panel["sx"] + (x * block_px)
    by = panel["sy"] + (z * block_px)

    rect = [bx, by, bx + block_px, by + block_px]

    base_background_color = _draw_base_path_cell(
        draw,
        cell["base_token"],
        rect
    )

    _draw_active_path_cell(
        img,
        draw,
        ctx,
        cell,
        rect,
        bx,
        by,
        base_background_color
    )

    _draw_path_cell_outline(
        draw,
        rect,
        cell["is_ghost"]
    )
    
def _draw_base_path_cell(draw, base_token: Token, layers: Layers) -> BackgroundColor:
    base_background_color = schematics_utils.get_background_color(
        base_token,
        default=(245, 245, 245)
    )

    draw.rectangle(
        layers,
        fill=base_background_color
    )

    return base_background_color

def _draw_active_path_cell(
    img,
    draw,
    ctx: SchematicContext,
    cell: Cell,
    layers: Layers,
    bx: int,
    by: int,
    base_background_color: BackgroundColor
):
    active_token = cell["active_token"]

    if active_token in ctx.topdown_textures:
        _paste_active_path_texture(
            img,
            ctx,
            active_token,
            bx,
            by,
            cell["is_ghost"]
        )
        return

    if active_token != "." and not cell["is_ground_layer"]:
        draw.rectangle(
            layers,
            fill=schematics_utils.get_background_color(
                active_token,
                default=base_background_color
            )
        )
        
def _paste_active_path_texture(
    img,
    ctx: SchematicContext,
    active_token: Token,
    bx: int,
    by: int,
    is_ghost: bool
):
    tex = schematics_utils.get_texture_for_render(
        active_token,
        ctx.topdown_textures[active_token]
    )

    if is_ghost:
        ghost_alpha = tex.split()[3].point(
            lambda p: int(p * 0.45)
        )

        img.paste(
            tex,
            (bx, by),
            ghost_alpha
        )
        return

    img.paste(
        tex,
        (bx, by),
        tex if tex.mode == "RGBA" else None
    )
    
def _draw_path_cell_outline(draw, layers: Layers, is_ghost: bool):
    draw.rectangle(
        layers,
        outline=(40, 40, 40, 12 if is_ghost else 25)
    )
    
def _build_path_output_path(ctx: SchematicContext) -> str:
    return (
        ctx.output_dir
        / f"{ctx.name.lower().replace(' ', '_')}_site_topdown.png"
    )

def render_path_focused_blueprint(ctx: SchematicContext):
    layout = _build_path_layout(ctx)
    siteLayer = landscape_utils.generate_landscape_y_minus_1_sitelayer(ctx)

    img, draw = _create_path_image(layout)

    _draw_path_title(draw, layout)

    for col_idx, layer_y in enumerate(layout["layers"]):
        panel = _get_path_panel_position(col_idx, layout)

        _draw_path_layer_header(draw, layer_y, panel)

        _draw_path_layer_panel(
            img,
            draw,
            ctx,
            layer_y,
            panel,
            layout,
            siteLayer
        )

    output_path = _build_path_output_path(ctx)
    img.save(output_path)