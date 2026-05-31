from collections.abc import Callable
from typing import Any

from PIL import Image

SpriteComposer = Callable[..., Image.Image]

_COMPOSERS: dict[str, SpriteComposer] = {}


def register_composer(behavior: str, composer: SpriteComposer) -> None:
    _COMPOSERS[behavior] = composer


def get_composer(behavior: str) -> SpriteComposer | None:
    return _COMPOSERS.get(behavior)


def compose_for_entry(
    behavior: str,
    *,
    size: int,
    **kwargs: Any,
) -> Image.Image | None:
    composer = get_composer(behavior)

    if composer is None:
        return None

    return composer(size=size, **kwargs)
