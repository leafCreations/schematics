from collections import Counter
from pathlib import Path

from helpers.context import SchematicContext
from helpers.structure_tokens import ParsedToken, parse_structure_token
from helpers.types import MaterialsIconList, MaterialsList, ParsedTokenMaterialsList


def resolve_texture_path(ctx: SchematicContext, texture_name: str) -> Path:
    if texture_name.startswith("/custom/"):
        return ctx.assets_dir / "custom" / texture_name.removeprefix("/custom/")

    return ctx.assets_dir / texture_name


def resolve_material_texture_name(parsed: ParsedToken, ctx: SchematicContext) -> str:
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
        block_name = resolve_material_block_name(parsed, ctx)
        texture_name = f"{block_name}.png"

    if material:
        texture_name = texture_name.format(material=material)

    return texture_name


def collect_material_tokens(ctx: SchematicContext) -> ParsedTokenMaterialsList:
    parsed_tokens = []

    for layer in ctx.layers:
        for row in layer["cells"]:
            for raw_cell in row:
                parsed = parse_structure_token(raw_cell)

                if parsed is not None:
                    parsed_tokens.append(parsed)

    return parsed_tokens


def format_material_name(block_name: str) -> str:
    return block_name.replace("_", " ").title()


def resolve_material_block_name(parsed: ParsedToken, ctx: SchematicContext) -> str:
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


def should_count_material(parsed: ParsedToken, ctx: SchematicContext) -> bool:
    entry = ctx.block_registry[parsed.token]
    behavior = entry["behavior"]

    if behavior == "door" and parsed.variant == "upper":
        return False

    return not (behavior == "bed" and parsed.variant == "foot")


def build_material_inventory(
    parsed_tokens: ParsedTokenMaterialsList,
    ctx: SchematicContext,
) -> tuple[MaterialsList, MaterialsIconList]:
    material_counts = Counter()
    material_icons = {}

    for parsed in parsed_tokens:
        if not should_count_material(parsed, ctx):
            continue

        block_name = resolve_material_block_name(parsed, ctx)
        material_name = format_material_name(block_name)

        material_counts[material_name] += 1
        material_icons.setdefault(material_name, resolve_material_texture_name(parsed, ctx))

    materials = sorted(material_counts.items(), key=lambda item: item[0].lower())

    return materials, material_icons
