from helpers.log_orientation import orientation_to_axis, resolve_log_orientation
from helpers.structure_tokens import ParsedToken
from helpers.types import BlockRegistryEntry


def resolve_token_color(entry: BlockRegistryEntry, parsed: ParsedToken) -> str:
    defaults = entry.get("defaults", {})
    return (
        parsed.material
        or entry.get("color_default")
        or entry.get("material_default")
        or defaults.get("color")
        or "red"
    )


def resolve_token_fields(
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
) -> tuple[str | None, str | None, str | None, dict]:
    defaults = entry.get("defaults", {})
    material = parsed.material or entry.get("material_default")
    direction = parsed.direction or defaults.get("direction")
    variant = parsed.variant or defaults.get("variant")
    return material, direction, variant, defaults


def resolve_minecraft_block_id(entry: BlockRegistryEntry, parsed: ParsedToken) -> str:
    material, _direction, variant, _defaults = resolve_token_fields(entry, parsed)
    minecraft = entry["minecraft"]

    if "variants" in minecraft:
        if variant is None:
            raise ValueError(f"{parsed.token} requires a variant or defaults.variant")

        block_name = minecraft["variants"][variant]["block"]
    else:
        block_name = minecraft["block"]

    if material and "{material}" in block_name:
        block_name = block_name.format(material=material)

    color = resolve_token_color(entry, parsed)
    if "{color}" in block_name:
        block_name = block_name.format(color=color)

    return block_name


def resolve_minecraft_blockstates(
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
    blockstates_template: dict,
) -> dict[str, str]:
    material, direction, variant, defaults = resolve_token_fields(entry, parsed)

    color = resolve_token_color(entry, parsed)

    format_values = {
        **defaults,
        "material": material,
        "color": color,
        "direction": direction,
        "variant": variant,
        "half": parsed.variant or defaults.get("half"),
        "part": parsed.variant or defaults.get("part"),
        "type": parsed.variant or defaults.get("type"),
        "shape": parsed.variant or defaults.get("shape"),
    }

    for state_key, state_value in parsed.states:
        if isinstance(state_value, bool):
            format_values[state_key] = "true" if state_value else "false"
        else:
            format_values[state_key] = str(state_value)

    if entry.get("behavior") == "log":
        orientation = resolve_log_orientation(parsed, entry)
        format_values["orientation"] = orientation
        format_values["axis"] = orientation_to_axis(orientation)

    resolved_blockstates: dict[str, str] = {}

    for state_name, state_value in blockstates_template.items():
        if isinstance(state_value, str):
            resolved_value = state_value.format(**format_values)
        else:
            resolved_value = state_value

        resolved_blockstates[state_name] = str(resolved_value).lower()

    return resolved_blockstates


def get_block_behavior(entry: BlockRegistryEntry) -> str:
    return entry.get("behavior", "solid")
