from dataclasses import dataclass
from typing import TypeAlias

EMPTY_CELL = "."
BlockStateValue: TypeAlias = str | bool
BlockStates: TypeAlias = tuple[tuple[str, BlockStateValue], ...]

_KNOWN_STATE_KEYS = frozenset({"hanging", "open"})


@dataclass(frozen=True)
class ParsedToken:
    token: str
    material: str | None = None
    direction: str | None = None
    variant: str | None = None
    rotation: int = 0
    states: BlockStates = ()


def _is_states_clause(suffix: str) -> bool:
    for part in suffix.split(","):
        part = part.strip()

        if not part:
            continue

        if "=" in part:
            key, _value = part.split("=", 1)
            key = key.strip()

            if key not in _KNOWN_STATE_KEYS:
                return False
        elif part not in _KNOWN_STATE_KEYS:
            return False

    return True


def _split_states_suffix(token_text: str) -> tuple[str, str]:
    if ";" not in token_text:
        return token_text, ""

    base, _, suffix = token_text.rpartition(";")

    if not suffix or not _is_states_clause(suffix):
        return token_text, ""

    return base, suffix


def parse_block_states(states_text: str) -> BlockStates:
    states: list[tuple[str, BlockStateValue]] = []

    for part in states_text.split(","):
        part = part.strip()

        if not part:
            continue

        if "=" in part:
            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip().lower()

            if value in {"true", "yes", "1"}:
                states.append((key, True))
            elif value in {"false", "no", "0"}:
                states.append((key, False))
            else:
                states.append((key, value))
        else:
            states.append((part, True))

    return tuple(states)


def format_block_states(states: BlockStates) -> str:
    parts: list[str] = []

    for key, value in states:
        if isinstance(value, bool):
            parts.append(f"{key}={str(value).lower()}")
        else:
            parts.append(f"{key}={value}")

    return ",".join(parts)


def format_structure_token(parsed: ParsedToken) -> str:
    token = parsed.token

    if parsed.material:
        token = f"{token}:{parsed.material}"

    if parsed.direction:
        token = f"{token}@{parsed.direction}"

    if parsed.variant:
        token = f"{token}#{parsed.variant}"

    if parsed.states:
        token = f"{token};{format_block_states(parsed.states)}"

    if parsed.rotation:
        token = f"{token}!{parsed.rotation}"

    return token


def parse_structure_token(raw: str) -> ParsedToken | None:
    if raw == EMPTY_CELL:
        return None

    token_text, _, rotation_text = raw.partition("!")

    rotation = int(rotation_text) if rotation_text else 0

    main_text, states_text = _split_states_suffix(token_text)
    states = parse_block_states(states_text) if states_text else ()

    token_part, _, variant = main_text.partition("#")
    token_material, _, direction = token_part.partition("@")
    token, _, material = token_material.partition(":")

    return ParsedToken(
        token=token,
        material=material or None,
        direction=direction or None,
        variant=variant or None,
        rotation=rotation,
        states=states,
    )
