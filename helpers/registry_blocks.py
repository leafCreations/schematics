from helpers.structure_tokens import ParsedToken
from helpers.types import BlockRegistryEntry


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

    if material:
        block_name = block_name.format(material=material)

    return block_name


def resolve_minecraft_blockstates(
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
    blockstates_template: dict,
) -> dict[str, str]:
    material, direction, variant, defaults = resolve_token_fields(entry, parsed)

    format_values = {
        **defaults,
        **dict(parsed.states),
        "material": material,
        "direction": direction,
        "variant": variant,
        "half": parsed.variant or defaults.get("half"),
        "part": parsed.variant or defaults.get("part"),
        "type": parsed.variant or defaults.get("type"),
        "shape": parsed.variant or defaults.get("shape"),
    }

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
