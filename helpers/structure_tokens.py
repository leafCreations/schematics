from dataclasses import dataclass
from typing import TypeAlias

EMPTY_CELL = "."
BlockStateValue: TypeAlias = str | bool
BlockStates: TypeAlias = tuple[tuple[str, BlockStateValue], ...]


@dataclass(frozen=True)
class ParsedToken:
    token: str
    material: str | None = None
    direction: str | None = None
    variant: str | None = None
    states: BlockStates = ()


def parse_structure_token(raw: str) -> ParsedToken | None:
    if raw == EMPTY_CELL:
        return None

    token_part, _, variant = raw.partition("#")
    token_material, _, direction = token_part.partition("@")
    token, _, material = token_material.partition(":")

    return ParsedToken(
        token=token,
        material=material or None,
        direction=direction or None,
        variant=variant or None,
    )
