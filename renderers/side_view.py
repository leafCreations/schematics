import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from PIL import Image, ImageDraw

def render_structure_elevations(ctx: SchematicContext):
    top_margin = 60
    panel_w = max(ctx.struct_w, ctx.struct_h) * 30
    panel_h = 6 * 30

    img_w = (panel_w * 4) + (50 * 5)
    img_h = top_margin + panel_h + 60

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.text(
        (50, 20),
        "STRUCTURE SIDE-VIEW ELEVATIONS - ISOLATED BUILDING FAÇADES PROFILE",
        fill=(30, 30, 30)
    )

    struct_elevations = {
        k: {y: [] for y in range(6)}
        for k in ["N", "S", "W", "E"]
    }

    for y in range(6):
        for x in range(ctx.struct_w):
            fn, fs = ".", "."

            for z in range(ctx.struct_h):
                raw_token = ctx.data[y][z].split()[x]
                token, _direction = schematics_utils.resolve_schematic_token(raw_token)

                if token != ".":
                    fn = raw_token.split("@")[0]
                    break

            for z in range(ctx.struct_h - 1, -1, -1):
                raw_token = ctx.data[y][z].split()[x]
                token, _direction = schematics_utils.resolve_schematic_token(raw_token)

                if token != ".":
                    fs = raw_token.split("@")[0]
                    break

            struct_elevations["N"][y].append(fn)
            struct_elevations["S"][y].append(fs)

        for z in range(ctx.struct_h):
            fw, fe = ".", "."
            tokens = ctx.data[y][z].split()

            for x in range(ctx.struct_w):
                raw_token = tokens[x]
                token, _direction = schematics_utils.resolve_schematic_token(raw_token)

                if token != ".":
                    fw = raw_token.split("@")[0]
                    break

            for x in range(ctx.struct_w - 1, -1, -1):
                raw_token = tokens[x]
                token, _direction = schematics_utils.resolve_schematic_token(raw_token)

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
    current_x = 50
    current_y = top_margin + 20

    for idx, view_key in enumerate(keys):
        draw.text(
            (current_x, current_y - 20),
            headings[idx],
            fill=(60, 60, 60)
        )

        p_data = struct_elevations[view_key]
        tokens_count = ctx.struct_w if view_key in ["N", "S"] else ctx.struct_h

        for layer_y in range(6):
            pixel_row = 5 - layer_y
            tokens = p_data[layer_y]

            for col in range(tokens_count):
                raw_token = tokens[col] if col < len(tokens) else "."
                token, _direction = schematics_utils.resolve_schematic_token(raw_token)

                bx = current_x + (col * 30)
                by = current_y + (pixel_row * 30)

                if token == ".":
                    draw.rectangle(
                        [bx, by, bx + 30, by + 30],
                        fill=(240, 248, 255)
                    )
                    continue

                rendered = schematics_utils.paste_side_view_token(
                    img,
                    ctx.sideview_textures,
                    raw_token,
                    (bx, by),
                    30,
                    view_key
                )

                if not rendered:
                    draw.rectangle(
                        [bx, by, bx + 30, by + 30],
                        fill=schematics_utils.get_background_color(token, default=(230, 230, 230))
                    )

        current_x += panel_w + 50

    img.save(ctx.output_dir / f"{ctx.name.lower().replace(' ', '_')}_house_facades.png")    