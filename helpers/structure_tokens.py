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
    rotation: int = 0
    states: BlockStates = ()


def parse_structure_token(raw: str) -> ParsedToken | None:
    if raw == EMPTY_CELL:
        return None

    token_text, _, rotation_text = raw.partition("!")

    rotation = int(rotation_text) if rotation_text else 0

    token_part, _, variant = token_text.partition("#")
    token_material, _, direction = token_part.partition("@")
    token, _, material = token_material.partition(":")

    return ParsedToken(
        token=token,
        material=material or None,
        direction=direction or None,
        variant=variant or None,
        rotation=rotation,
    )
