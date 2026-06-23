from collections.abc import Callable
from pathlib import Path

from PIL import Image

from helpers.paths import resolve_generated_assets_folder

BakeFn = Callable[[], Image.Image]


def _generated_root(generated_root: Path | None) -> Path:
    if generated_root is not None:
        return generated_root
    return resolve_generated_assets_folder()


def sanitize_cache_key(key: str) -> str:
    """Return a filesystem-safe cache key while staying deterministic."""
    return (
        key.replace(":", "_")
        .replace("@", "_at_")
        .replace("#", "_")
        .replace(";", "_")
        .replace("=", "_eq_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def cache_path(view: str, key: str, *, generated_root: Path | None = None) -> Path:
    safe_key = sanitize_cache_key(key)
    return _generated_root(generated_root) / view / f"{safe_key}.png"


def load_cached(
    view: str,
    key: str,
    *,
    generated_root: Path | None = None,
) -> Image.Image | None:
    path = cache_path(view, key, generated_root=generated_root)

    if not path.exists():
        return None

    return Image.open(path).convert("RGBA")


def save_cached(
    view: str,
    key: str,
    image: Image.Image,
    *,
    generated_root: Path | None = None,
) -> Path:
    path = cache_path(view, key, generated_root=generated_root)
    path.parent.mkdir(parents=True, exist_ok=True)

    if image.mode != "RGBA":
        image = image.convert("RGBA")

    image.save(path)
    return path


def load_or_bake(
    view: str,
    key: str,
    bake_fn: BakeFn,
    *,
    generated_root: Path | None = None,
    force: bool = False,
) -> Image.Image:
    root = _generated_root(generated_root)

    if not force:
        cached = load_cached(view, key, generated_root=root)

        if cached is not None:
            return cached

    image = bake_fn()

    if image.mode != "RGBA":
        image = image.convert("RGBA")

    save_cached(view, key, image, generated_root=root)
    return image


def load_generated_sprite(
    view: str,
    key: str,
    block_px: int,
    *,
    generated_root: Path | None = None,
) -> Image.Image | None:
    cached = load_cached(view, key, generated_root=generated_root)

    if cached is None:
        return None

    if cached.size != (block_px, block_px):
        return cached.resize((block_px, block_px), Image.Resampling.NEAREST)

    return cached
