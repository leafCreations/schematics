from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

import helpers.registry_blocks as registry_blocks
import helpers.utils as utils
from helpers.block_catalog import catalog_display_name
from helpers.context import SchematicContext
from helpers.layer_groups import is_layer_render_visible
from helpers.paths import ASSET_FOLDER, GENERATED_ASSETS_FOLDER, resolve_project_custom_folder
from helpers.registry_lookup import (
    get_block_entry,
    is_minecraft_block_token,
    load_catalog_texture_image,
)
from helpers.sprite_baker.cache import load_cached
from helpers.sprite_baker.compose_slab import resolve_slab_placement
from helpers.sprite_baker.compose_trapdoor import resolve_trapdoor_half
from helpers.sprite_baker.runtime_bake import load_or_bake_generated_sprite
from helpers.sprite_baker.stair_shapes import STAIR_SHAPES
from helpers.structure_tokens import ParsedToken, format_structure_token, parse_structure_token
from helpers.types import (
    MaterialsIconList,
    MaterialsIconTokens,
    MaterialsList,
    ParsedTokenMaterialsList,
    RawToken,
)
from helpers.utils_schematics import (
    corner_stair_facing_rotation,
    get_texture_for_render,
    is_corner_stair_shape,
    resolve_token_for_render,
)
from registries.loader import resolve_registry_texture_filename

GENERATED_ICON_PREFIX = "generated:"
BAKEABLE_INVENTORY_BEHAVIORS = frozenset(
    {
        "slab",
        "stairs",
        "bed",
        "chest",
        "fence",
        "wall",
        "torch",
        "lantern",
        "log",
        "door",
        "trapdoor",
    }
)
INVENTORY_VIEW_BEHAVIORS = frozenset(
    {"bed", "fence", "wall", "torch", "lantern", "stairs", "door", "trapdoor"}
)


def resolve_texture_path(ctx: SchematicContext, texture_name: str) -> Path:
    if texture_name.startswith("/custom/"):
        return resolve_project_custom_folder() / texture_name.removeprefix("/custom/")

    if texture_name.startswith("/item/"):
        return ASSET_FOLDER / "textures" / "item" / texture_name.removeprefix("/item/")

    return ctx.assets_dir / texture_name


def resolve_material_texture_name(parsed: ParsedToken, ctx: SchematicContext) -> str:
    entry = get_block_entry(parsed)

    if entry is None:
        raise ValueError(f"Unknown block token: {parsed.token}")

    defaults = entry.get("defaults", {})

    material = parsed.material or entry.get("material_default")
    variant = parsed.variant or defaults.get("variant")

    render = entry.get("render", {})
    inventory_image = render.get("inventory_image")

    if inventory_image:
        texture_name = inventory_image
    else:
        texture_name = resolve_registry_texture_filename(
            entry,
            "top",
            material=material,
            variant=variant,
        )

        if texture_name is None:
            block_name = resolve_material_block_name(parsed, ctx)
            texture_name = f"{block_name}.png"

    if material and isinstance(texture_name, str):
        texture_name = texture_name.format(material=material)

    return texture_name


def resolve_material_sprite_key(parsed: ParsedToken, ctx: SchematicContext) -> str | None:
    entry = get_block_entry(parsed)

    if entry is None:
        return None

    behavior = registry_blocks.get_block_behavior(entry)

    if behavior not in BAKEABLE_INVENTORY_BEHAVIORS:
        return None

    key = parsed.token

    if behavior == "stairs":
        material = parsed.material or entry.get("material_default")
        if material:
            key = f"{key}:{material}"

        shape = (
            parsed.variant
            if parsed.variant in STAIR_SHAPES
            else entry.get("defaults", {}).get("shape", "straight")
        )

        if shape and shape != "straight":
            key = f"{key}#{shape}"
    elif behavior == "slab":
        material = parsed.material or entry.get("material_default")
        if material:
            key = f"{key}:{material}"

        placement = resolve_slab_placement(parsed.variant, entry)

        if placement == "top":
            key = f"{key}#top"
    elif behavior == "trapdoor":
        material = parsed.material or entry.get("material_default")
        if material:
            key = f"{key}:{material}"

        half = resolve_trapdoor_half(parsed.variant, entry)

        if half == "top":
            key = f"{key}#top"
    elif behavior == "bed":
        color = registry_blocks.resolve_token_color(entry, parsed)
        key = f"{key}:{color}"
    elif behavior == "fence" or behavior == "wall":
        material = parsed.material or entry.get("material_default")
        if material:
            key = f"{key}:{material}"
    elif behavior in {"torch", "lantern"}:
        variant = parsed.variant or entry.get("defaults", {}).get("variant", "normal")
        if variant and variant != "normal":
            key = f"{key}#{variant}"
    elif behavior == "log" or behavior == "door":
        material = parsed.material or entry.get("material_default")
        if material:
            key = f"{key}:{material}"

    return key


def _behavior_for_sprite_key(sprite_key: str, ctx: SchematicContext) -> str | None:
    parsed = parse_structure_token(sprite_key)

    if parsed is None:
        return None

    entry = get_block_entry(parsed)

    if entry is None:
        return None

    return registry_blocks.get_block_behavior(entry)


def _inventory_behavior(
    *,
    sprite_key: str | None = None,
    parsed: ParsedToken | None = None,
    ctx: SchematicContext,
) -> str | None:
    if parsed is not None:
        entry = get_block_entry(parsed) or {}
        return registry_blocks.get_block_behavior(entry)

    if sprite_key is not None:
        return _behavior_for_sprite_key(sprite_key, ctx)

    return None


def _generated_inventory_view(behavior: str | None) -> str:
    if behavior == "stairs":
        return "side"

    if behavior in INVENTORY_VIEW_BEHAVIORS:
        return "inventory"

    return "top"


def _is_generated_inventory_icon(icon: str) -> bool:
    return icon.startswith(GENERATED_ICON_PREFIX)


def _inventory_icon_priority(icon: str, parsed: ParsedToken, entry: dict) -> tuple[int, int]:
    generated = int(_is_generated_inventory_icon(icon))
    shaped = 0

    if registry_blocks.get_block_behavior(entry) == "stairs":
        shape = parsed.variant or entry.get("defaults", {}).get("shape", "straight")
        shaped = int(shape != "straight")

    return (generated, shaped)


def _should_replace_inventory_icon(
    current_icon: str,
    current_parsed: ParsedToken,
    current_entry: dict,
    new_icon: str,
    new_parsed: ParsedToken,
    new_entry: dict,
) -> bool:
    return _inventory_icon_priority(new_icon, new_parsed, new_entry) > _inventory_icon_priority(
        current_icon,
        current_parsed,
        current_entry,
    )


def _prepare_generated_inventory_icon(
    tex: Image.Image,
    parsed: ParsedToken,
    entry: dict,
    raw_token: RawToken | None = None,
) -> Image.Image:
    if raw_token is not None:
        _, direction = resolve_token_for_render(raw_token)
    else:
        direction = utils.normalize_direction(
            parsed.direction or entry.get("defaults", {}).get("direction")
        )

    behavior = registry_blocks.get_block_behavior(entry)

    if behavior != "stairs" and is_corner_stair_shape(parsed, entry):
        facing_rotation = corner_stair_facing_rotation(direction)
        if facing_rotation:
            tex = utils.rotate_texture_by_degrees(tex, facing_rotation)

    if parsed.rotation:
        tex = utils.rotate_texture_by_degrees(tex, parsed.rotation)

    return tex


def resolve_material_inventory_icon(parsed: ParsedToken, ctx: SchematicContext) -> str:
    sprite_key = resolve_material_sprite_key(parsed, ctx)
    entry = get_block_entry(parsed) or {}
    behavior = registry_blocks.get_block_behavior(entry)

    if sprite_key is not None:
        if behavior in INVENTORY_VIEW_BEHAVIORS:
            return f"{GENERATED_ICON_PREFIX}{sprite_key}"

        view = _generated_inventory_view(behavior)

        if behavior in BAKEABLE_INVENTORY_BEHAVIORS:
            from helpers import constants

            if (
                load_or_bake_generated_sprite(
                    view,
                    sprite_key,
                    constants.BLOCK_PX,
                    behavior=behavior,
                    textures_dir=ctx.assets_dir,
                    generated_root=GENERATED_ASSETS_FOLDER,
                )
                is not None
            ):
                return f"{GENERATED_ICON_PREFIX}{sprite_key}"
        elif load_cached(view, sprite_key, generated_root=GENERATED_ASSETS_FOLDER):
            return f"{GENERATED_ICON_PREFIX}{sprite_key}"

        if (
            behavior not in INVENTORY_VIEW_BEHAVIORS
            and view != "top"
            and load_cached("top", sprite_key, generated_root=GENERATED_ASSETS_FOLDER)
        ):
            return f"{GENERATED_ICON_PREFIX}{sprite_key}"

    return resolve_material_texture_name(parsed, ctx)


def collect_raw_tokens_from_layers(layers: list[dict]) -> list[RawToken]:
    """Flatten non-empty cells from all layer grids (editor and previews)."""
    tokens: list[RawToken] = []

    for layer in layers:
        for row in layer.get("cells", []):
            for raw_cell in row:
                if raw_cell and raw_cell != ".":
                    tokens.append(raw_cell)

    return tokens


def collect_material_tokens(ctx: SchematicContext) -> ParsedTokenMaterialsList:
    parsed_tokens = []

    for layer_array_index, layer in enumerate(ctx.layers):
        if not is_layer_render_visible(layer, layer_array_index, ctx.grid):
            continue

        for row in layer["cells"]:
            for raw_cell in row:
                parsed = parse_structure_token(raw_cell)

                if parsed is not None:
                    parsed_tokens.append(parsed)

    return parsed_tokens


def format_material_name(block_name: str) -> str:
    return block_name.replace("_", " ").title()


def resolve_material_display_name(parsed: ParsedToken, ctx: SchematicContext) -> str:
    entry = get_block_entry(parsed)

    if entry is None:
        return format_material_name(parsed.token)

    block_id = registry_blocks.resolve_minecraft_block_id(entry, parsed)

    if registry_blocks.get_block_behavior(entry) == "bed":
        color = registry_blocks.resolve_token_color(entry, parsed)
        color_display = catalog_display_name(f"minecraft:{color}_bed")
        if color_display is not None:
            return color_display

    display_name = catalog_display_name(block_id)

    if display_name is not None:
        return display_name

    return format_material_name(block_id.split(":", 1)[-1])


def resolve_material_block_name(parsed: ParsedToken, ctx: SchematicContext) -> str:
    entry = get_block_entry(parsed)

    if entry is None:
        return parsed.token.lower()

    block_name = registry_blocks.resolve_minecraft_block_id(entry, parsed)
    return block_name.split(":", 1)[-1]


def should_count_material(parsed: ParsedToken, ctx: SchematicContext) -> bool:
    entry = get_block_entry(parsed)

    if entry is None:
        return False

    behavior = registry_blocks.get_block_behavior(entry)

    if behavior == "door" and parsed.variant == "upper":
        return False

    return not (behavior == "bed" and parsed.variant == "foot")


def build_material_inventory(
    parsed_tokens: ParsedTokenMaterialsList,
    ctx: SchematicContext,
    *,
    raw_tokens: list[RawToken] | None = None,
) -> tuple[MaterialsList, MaterialsIconList, MaterialsIconTokens]:
    material_counts = Counter()
    material_icons: MaterialsIconList = {}
    material_icon_tokens: MaterialsIconTokens = {}

    token_pairs = (
        zip(raw_tokens, parsed_tokens, strict=True)
        if raw_tokens is not None
        else ((None, parsed) for parsed in parsed_tokens)
    )

    for _raw_token, parsed in token_pairs:
        if not should_count_material(parsed, ctx):
            continue

        entry = get_block_entry(parsed)

        if entry is None:
            continue

        material_name = resolve_material_display_name(parsed, ctx)
        icon = resolve_material_inventory_icon(parsed, ctx)

        material_counts[material_name] += 1

        if material_name not in material_icons:
            material_icons[material_name] = icon
            material_icon_tokens[material_name] = parsed
            continue

        if _should_replace_inventory_icon(
            material_icons[material_name],
            material_icon_tokens[material_name],
            get_block_entry(material_icon_tokens[material_name]) or {},
            icon,
            parsed,
            entry,
        ):
            material_icons[material_name] = icon
            material_icon_tokens[material_name] = parsed

    materials = sorted(material_counts.items(), key=lambda item: item[0].lower())

    return materials, material_icons, material_icon_tokens


def build_material_inventory_from_raw_tokens(
    raw_tokens: list[RawToken],
    ctx: SchematicContext,
) -> tuple[MaterialsList, MaterialsIconList, MaterialsIconTokens]:
    parsed_tokens = [
        parsed
        for raw_token in raw_tokens
        if (parsed := parse_structure_token(raw_token)) is not None
    ]

    filtered_raw_tokens = [
        raw_token for raw_token in raw_tokens if parse_structure_token(raw_token) is not None
    ]

    return build_material_inventory(parsed_tokens, ctx, raw_tokens=filtered_raw_tokens)


def _inventory_tint_token(
    parsed: ParsedToken | None,
    raw_token: RawToken | None,
) -> str | None:
    if raw_token:
        return raw_token

    if parsed is not None:
        return format_structure_token(parsed)

    return None


def _apply_inventory_schematic_tint(
    tex: Image.Image,
    *,
    parsed: ParsedToken | None,
    raw_token: RawToken | None,
) -> Image.Image:
    tint_token = _inventory_tint_token(parsed, raw_token)

    if tint_token is None:
        return tex

    return get_texture_for_render(tint_token, tex)


def _paste_catalog_inventory_icon(
    img: Image.Image,
    parsed: ParsedToken,
    x: int,
    y: int,
    size: int,
    *,
    raw_token: RawToken | None = None,
) -> bool:
    if not is_minecraft_block_token(parsed):
        return False

    tex = load_catalog_texture_image(parsed, "top", size)

    if tex is None:
        return False

    tex = _apply_inventory_schematic_tint(tex, parsed=parsed, raw_token=raw_token)
    img.paste(tex, (x, y), tex)
    return True


def draw_inventory_icon(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    ctx: SchematicContext,
    texture_name: str | None,
    x: int,
    y: int,
    size: int = 25,
    *,
    parsed: ParsedToken | None = None,
    raw_token: RawToken | None = None,
) -> None:
    if texture_name and texture_name.startswith(GENERATED_ICON_PREFIX):
        sprite_key = texture_name.removeprefix(GENERATED_ICON_PREFIX)
        behavior = _inventory_behavior(sprite_key=sprite_key, parsed=parsed, ctx=ctx)

        view = _generated_inventory_view(behavior)

        if behavior in BAKEABLE_INVENTORY_BEHAVIORS:
            tex = load_or_bake_generated_sprite(
                view,
                sprite_key,
                size,
                behavior=behavior,
                textures_dir=ctx.assets_dir,
                generated_root=GENERATED_ASSETS_FOLDER,
            )
        else:
            from helpers.sprite_baker.cache import load_generated_sprite

            tex = load_generated_sprite(
                view,
                sprite_key,
                size,
                generated_root=GENERATED_ASSETS_FOLDER,
            )

        if tex is None and behavior not in INVENTORY_VIEW_BEHAVIORS and view != "top":
            tex = load_generated_sprite(
                "top",
                sprite_key,
                size,
                generated_root=GENERATED_ASSETS_FOLDER,
            )

        if tex is not None:
            if parsed is not None:
                entry = get_block_entry(parsed) or {}
                tex = _prepare_generated_inventory_icon(tex, parsed, entry, raw_token=raw_token)

            img.paste(tex, (x, y), tex)
            return

    if texture_name:
        texture_path = resolve_texture_path(ctx, texture_name)

        if texture_path.exists():
            tex = Image.open(texture_path).convert("RGBA")
            tex = tex.resize((size, size), resample=Image.Resampling.NEAREST)
            tex = _apply_inventory_schematic_tint(tex, parsed=parsed, raw_token=raw_token)
            img.paste(tex, (x, y), tex)
            return

    if parsed is not None and _paste_catalog_inventory_icon(
        img,
        parsed,
        x,
        y,
        size,
        raw_token=raw_token,
    ):
        return

    draw.rectangle(
        [x, y, x + size, y + size],
        fill=(230, 230, 230),
        outline=(80, 80, 80),
    )
