from __future__ import annotations

from dataclasses import replace

from helpers.block_catalog import normalize_block_id
from helpers.structure_tokens import ParsedToken, format_structure_token, parse_structure_token

CAMPFIRE_BLOCK_IDS = frozenset({"minecraft:campfire", "minecraft:soul_campfire"})
CAMPFIRE_FACINGS = ("north", "south", "east", "west")
LIT_STATE = "lit"
DEFAULT_CAMPFIRE_FACING = "south"
DEFAULT_CAMPFIRE_LIT = True


def is_campfire_block_id(block_id: str) -> bool:
    return normalize_block_id(block_id) in CAMPFIRE_BLOCK_IDS


def is_campfire_token(parsed: ParsedToken) -> bool:
    if parsed.token != "minecraft" or not parsed.material:
        return False

    return is_campfire_block_id(f"{parsed.token}:{parsed.material}")


def explicit_lit(parsed: ParsedToken) -> bool | None:
    for key, value in parsed.states:
        if key != LIT_STATE:
            continue

        if isinstance(value, bool):
            return value

        return str(value).lower() in {"true", "yes", "1"}

    return None


def resolve_campfire_facing(parsed: ParsedToken) -> str:
    direction = (parsed.direction or DEFAULT_CAMPFIRE_FACING).lower()

    if direction in CAMPFIRE_FACINGS:
        return direction

    return DEFAULT_CAMPFIRE_FACING


def resolve_campfire_lit(parsed: ParsedToken) -> bool:
    explicit = explicit_lit(parsed)

    if explicit is not None:
        return explicit

    return DEFAULT_CAMPFIRE_LIT


def campfire_block_entry(block_id: str) -> dict:
    normalized = normalize_block_id(block_id)

    return {
        "behavior": "campfire",
        "minecraft": {
            "block": normalized,
            "blockstates": {
                "facing": "{direction}",
                "lit": "{lit}",
            },
        },
        "defaults": {"direction": DEFAULT_CAMPFIRE_FACING, "lit": "true"},
    }


def with_campfire_lit(raw_token: str, lit_value: bool) -> str:
    parsed = parse_structure_token(raw_token)

    if parsed is None or not is_campfire_token(parsed):
        return raw_token

    other_states = tuple((key, value) for key, value in parsed.states if key != LIT_STATE)
    states = (*other_states, (LIT_STATE, lit_value))

    return format_structure_token(replace(parsed, states=states))
