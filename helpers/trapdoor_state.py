from __future__ import annotations

from dataclasses import replace

from helpers.structure_tokens import ParsedToken, format_structure_token, parse_structure_token

OPEN_STATE = "open"


def explicit_open(parsed: ParsedToken) -> bool | None:
    """Return an explicit ``open`` override, or ``None`` for the registry default."""
    for key, value in parsed.states:
        if key != OPEN_STATE:
            continue

        if isinstance(value, bool):
            return value

        return str(value).lower() in {"true", "yes", "1"}

    return None


def with_trapdoor_open(raw_token: str, open_value: bool) -> str:
    """Return ``raw_token`` with trapdoor ``open`` state replaced."""
    parsed = parse_structure_token(raw_token)

    if parsed is None or parsed.token != "TRAPDOOR":
        return raw_token

    other_states = tuple((key, value) for key, value in parsed.states if key != OPEN_STATE)
    states = (*other_states, (OPEN_STATE, open_value))

    return format_structure_token(replace(parsed, states=states))
