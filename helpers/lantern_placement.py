from __future__ import annotations

from helpers.cells import get_structure_cell
from helpers.context import SchematicContext
from helpers.registry_lookup import get_block_entry
from helpers.structure_tokens import ParsedToken, parse_structure_token

HANGING_STATE = "hanging"


def explicit_hanging(parsed: ParsedToken) -> bool | None:
    """Return a manual ``hanging`` override, or ``None`` when placement should be inferred."""
    for key, value in parsed.states:
        if key != HANGING_STATE:
            continue

        if isinstance(value, bool):
            return value

        return str(value).lower() in {"true", "yes", "1"}

    return None


def cell_supports_lantern_hang(raw_token: str) -> bool:
    """Return whether a non-empty cell above can support a hanging lantern."""
    if raw_token == ".":
        return False

    parsed = parse_structure_token(raw_token)

    if parsed is None:
        return False

    return get_block_entry(parsed) is not None


def infer_hanging_from_above(
    ctx: SchematicContext,
    layer_array_index: int,
    x: int,
    z: int,
) -> bool:
    above = get_structure_cell(ctx, layer_array_index + 1, x, z, empty=".")
    return cell_supports_lantern_hang(above)


def resolve_lantern_worldgen(
    parsed: ParsedToken,
    ctx: SchematicContext,
    layer_array_index: int,
    x: int,
    z: int,
) -> ParsedToken:
    hanging = explicit_hanging(parsed)

    if hanging is None:
        hanging = infer_hanging_from_above(ctx, layer_array_index, x, z)

    other_states = tuple((key, value) for key, value in parsed.states if key != HANGING_STATE)

    return ParsedToken(
        token=parsed.token,
        material=parsed.material,
        direction=parsed.direction,
        variant=parsed.variant,
        rotation=parsed.rotation,
        states=(*other_states, (HANGING_STATE, hanging)),
    )
