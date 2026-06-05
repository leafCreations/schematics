"""Test helpers for sprite-baker integration tests (token-scoped texture loading)."""

from __future__ import annotations

from collections.abc import Collection, Iterator
from contextlib import contextmanager
from pathlib import Path

from registries.loader import MappedTextureImages, TextureType


@contextmanager
def generated_assets_root(path: Path) -> Iterator[Path]:
    """Point loader and paths at a temporary generated-assets directory."""
    import helpers.paths as paths_module
    import registries.loader as loader_module

    previous_paths_root = paths_module.GENERATED_ASSETS_FOLDER
    previous_loader_root = loader_module.GENERATED_ASSETS_FOLDER
    paths_module.GENERATED_ASSETS_FOLDER = path
    loader_module.GENERATED_ASSETS_FOLDER = path
    try:
        yield path
    finally:
        paths_module.GENERATED_ASSETS_FOLDER = previous_paths_root
        loader_module.GENERATED_ASSETS_FOLDER = previous_loader_root


def compile_texture_tokens(
    texture_type: TextureType,
    assets_dir: str,
    block_px: int,
    tokens: Collection[str],
    *,
    generated_root: Path | None = None,
) -> MappedTextureImages:
    """Load only the requested tokens via the same path as compile_texture_set."""
    from registries.loader import (
        GENERATED_ASSETS_FOLDER,
        _build_registry_texture_mapping,
        _generated_bake_keys,
        _load_token_texture,
    )

    mapping = _build_registry_texture_mapping(texture_type)
    generated_keys = _generated_bake_keys(texture_type)
    root = generated_root or GENERATED_ASSETS_FOLDER
    loaded: MappedTextureImages = {}
    for token in tokens:
        texture = _load_token_texture(
            texture_type,
            token,
            mapping=mapping,
            assets_dir=assets_dir,
            block_px=block_px,
            generated_keys=generated_keys,
            generated_root=root,
        )
        if texture is not None:
            loaded[token] = texture
    return loaded
