"""Path strips (trim | randomized path | trim) along site x or z."""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Literal

from helpers.grid_placement import site_cell_in_structure_footprint
from helpers.site_ground import GRASS_BLOCK
from helpers.terrain_tokens import (
    DIRT_PATH_BLOCK,
    PATH_VARIETY_OPTIONS,
    PATH_VARIETY_WEIGHTS,
    TRIM_BLOCK,
    TRIM_BLOCK_OPTIONS,
    canonical_terrain_token,
    migrate_terrain_token,
)

DEFAULT_PATH_VARIETY_BLOCKS: tuple[str, ...] = PATH_VARIETY_OPTIONS

PATH_SURFACE_TOKENS = frozenset({DIRT_PATH_BLOCK, *PATH_VARIETY_OPTIONS})
DEFAULT_PATH_WIDTH = 3
DEFAULT_TRIM_WIDTH = 1
DEFAULT_PATH_ORIENTATION: PathOrientation = "horizontal"

PathOrientation = Literal["horizontal", "vertical"]
RandomPathFn = Callable[[], str]

_CANONICAL_PATH_VARIETY = {canonical_terrain_token(block): block for block in PATH_VARIETY_OPTIONS}
_CANONICAL_TRIM_OPTIONS = {canonical_terrain_token(block): block for block in TRIM_BLOCK_OPTIONS}


def is_path_surface_token(token: str, *, variety_blocks: list[str] | None = None) -> bool:
    canonical = canonical_terrain_token(token)

    if canonical == canonical_terrain_token(DIRT_PATH_BLOCK):
        return True

    allowed = (
        {canonical_terrain_token(block) for block in variety_blocks}
        if variety_blocks is not None
        else set(_CANONICAL_PATH_VARIETY)
    )

    return canonical in allowed


def is_trim_token(token: str, *, trim_block: str | None = None) -> bool:
    return canonical_terrain_token(token) == canonical_terrain_token(trim_block or TRIM_BLOCK)


def is_legacy_trim_token(token: str) -> bool:
    return canonical_terrain_token(token) in _CANONICAL_TRIM_OPTIONS


def is_path_related_token(token: str, *, variety_blocks: list[str] | None = None) -> bool:
    return is_path_surface_token(token, variety_blocks=variety_blocks) or is_legacy_trim_token(
        token,
    )


def resolve_trim_block(grid: dict) -> str:
    block = migrate_terrain_token(str(grid.get("trim_block", TRIM_BLOCK)))
    return _CANONICAL_TRIM_OPTIONS.get(canonical_terrain_token(block), TRIM_BLOCK)


def resolve_path_variety_blocks(grid: dict) -> list[str]:
    raw = grid.get("path_variety_blocks")

    if not isinstance(raw, list) or not raw:
        return list(DEFAULT_PATH_VARIETY_BLOCKS)

    blocks: list[str] = []

    for block in raw:
        if not isinstance(block, str):
            continue

        canonical = canonical_terrain_token(block)
        catalog_block = _CANONICAL_PATH_VARIETY.get(canonical)

        if catalog_block is not None:
            blocks.append(catalog_block)

    return blocks or list(DEFAULT_PATH_VARIETY_BLOCKS)


DIRT_PATH_WEIGHT = 0.60


def random_path_block(
    rng: random.Random | None = None,
    *,
    variety_blocks: list[str] | None = None,
) -> str:
    """Return a path surface token; ``DIRT_PATH`` keeps fixed weight, variety fills the rest."""
    if variety_blocks is not None:
        selected = [block for block in variety_blocks if block in PATH_VARIETY_OPTIONS]
    else:
        selected = list(DEFAULT_PATH_VARIETY_BLOCKS)

    if not selected:
        return DIRT_PATH_BLOCK

    variety_weight = sum(PATH_VARIETY_WEIGHTS[block] for block in selected)
    total = DIRT_PATH_WEIGHT + variety_weight

    if total <= 0:
        return DIRT_PATH_BLOCK

    roll = (rng or random).random() * total

    if roll < DIRT_PATH_WEIGHT:
        return DIRT_PATH_BLOCK

    roll -= DIRT_PATH_WEIGHT
    cursor = 0.0

    for block in selected:
        weight = PATH_VARIETY_WEIGHTS[block]
        cursor += weight

        if roll < cursor:
            return block

    return selected[-1]


def resolve_path_width(grid: dict) -> int:
    width = int(grid.get("path_width", DEFAULT_PATH_WIDTH))
    return max(1, width)


def resolve_path_orientation(grid: dict) -> PathOrientation:
    orientation = grid.get("path_orientation", DEFAULT_PATH_ORIENTATION)

    if orientation in ("horizontal", "vertical"):
        return orientation  # type: ignore[return-value]

    return DEFAULT_PATH_ORIENTATION


def path_strip_bounds(
    center: int,
    path_width: int,
    *,
    trim_width: int = DEFAULT_TRIM_WIDTH,
) -> tuple[int, int, int, int]:
    """Return path min/max and trim min/max (inclusive) centered on ``center``."""
    path_start = center - path_width // 2
    path_end = path_start + path_width - 1
    trim_start = path_start - trim_width
    trim_end = path_end + trim_width
    return path_start, path_end, trim_start, trim_end


def paint_path_row(
    row: list[str],
    center_x: int,
    path_width: int,
    site_z: int,
    *,
    offset_x: int = 0,
    offset_z: int = 0,
    structure_width: int = 0,
    structure_depth: int = 0,
    trim_width: int = DEFAULT_TRIM_WIDTH,
    trim_block: str = TRIM_BLOCK,
    variety_blocks: list[str] | None = None,
    rng: random.Random | None = None,
) -> int:
    """Paint trim | path | trim along one site row (east–west). Returns cells painted."""
    path_left, path_right, trim_left, trim_right = path_strip_bounds(
        center_x,
        path_width,
        trim_width=trim_width,
    )
    painted = 0

    for x in range(len(row)):
        if site_cell_in_structure_footprint(
            x,
            site_z,
            offset_x=offset_x,
            offset_z=offset_z,
            structure_width=structure_width,
            structure_depth=structure_depth,
        ):
            continue

        if path_left <= x <= path_right:
            row[x] = random_path_block(rng, variety_blocks=variety_blocks)
            painted += 1
        elif trim_left <= x <= trim_right:
            row[x] = trim_block
            painted += 1

    return painted


def paint_path_column(
    site_ground: list[list[str]],
    site_x: int,
    center_z: int,
    path_width: int,
    *,
    offset_x: int = 0,
    offset_z: int = 0,
    structure_width: int = 0,
    structure_depth: int = 0,
    trim_width: int = DEFAULT_TRIM_WIDTH,
    trim_block: str = TRIM_BLOCK,
    variety_blocks: list[str] | None = None,
    rng: random.Random | None = None,
) -> int:
    """Paint trim | path | trim along one site column (north–south). Returns cells painted."""
    if site_x < 0:
        return 0

    path_top, path_bottom, trim_top, trim_bottom = path_strip_bounds(
        center_z,
        path_width,
        trim_width=trim_width,
    )
    painted = 0

    for z, row in enumerate(site_ground):
        if site_x >= len(row):
            continue

        if site_cell_in_structure_footprint(
            site_x,
            z,
            offset_x=offset_x,
            offset_z=offset_z,
            structure_width=structure_width,
            structure_depth=structure_depth,
        ):
            continue

        if path_top <= z <= path_bottom:
            row[site_x] = random_path_block(rng, variety_blocks=variety_blocks)
            painted += 1
        elif trim_top <= z <= trim_bottom:
            row[site_x] = trim_block
            painted += 1

    return painted


def paint_path_at_site(
    site_ground: list[list[str]],
    site_x: int,
    site_z: int,
    path_width: int,
    *,
    orientation: PathOrientation = DEFAULT_PATH_ORIENTATION,
    offset_x: int = 0,
    offset_z: int = 0,
    structure_width: int = 0,
    structure_depth: int = 0,
    trim_width: int = DEFAULT_TRIM_WIDTH,
    trim_block: str = TRIM_BLOCK,
    variety_blocks: list[str] | None = None,
    rng: random.Random | None = None,
) -> bool:
    """Paint a path strip; returns False if the anchor cell is on the structure footprint."""
    if site_z < 0 or site_z >= len(site_ground):
        return False

    row = site_ground[site_z]

    if site_x < 0 or site_x >= len(row):
        return False

    if site_cell_in_structure_footprint(
        site_x,
        site_z,
        offset_x=offset_x,
        offset_z=offset_z,
        structure_width=structure_width,
        structure_depth=structure_depth,
    ):
        return False

    footprint = {
        "offset_x": offset_x,
        "offset_z": offset_z,
        "structure_width": structure_width,
        "structure_depth": structure_depth,
    }
    strip_kwargs = {
        **footprint,
        "trim_block": trim_block,
        "variety_blocks": variety_blocks,
    }

    if orientation == "vertical":
        painted = paint_path_column(
            site_ground,
            site_x,
            site_z,
            path_width,
            **strip_kwargs,
            trim_width=trim_width,
            rng=rng,
        )
    else:
        painted = paint_path_row(
            row,
            site_x,
            path_width,
            site_z,
            **strip_kwargs,
            trim_width=trim_width,
            rng=rng,
        )

    return painted > 0


def _erase_all_path_cells_on_row(
    row: list[str],
    site_z: int,
    *,
    offset_x: int,
    offset_z: int,
    structure_width: int,
    structure_depth: int,
) -> int:
    erased = 0

    for x in range(len(row)):
        if site_cell_in_structure_footprint(
            x,
            site_z,
            offset_x=offset_x,
            offset_z=offset_z,
            structure_width=structure_width,
            structure_depth=structure_depth,
        ):
            continue

        if is_path_related_token(row[x]):
            row[x] = GRASS_BLOCK
            erased += 1

    return erased


def _erase_all_path_cells_on_column(
    site_ground: list[list[str]],
    site_x: int,
    *,
    offset_x: int,
    offset_z: int,
    structure_width: int,
    structure_depth: int,
) -> int:
    erased = 0

    for z, row in enumerate(site_ground):
        if site_x >= len(row):
            continue

        if site_cell_in_structure_footprint(
            site_x,
            z,
            offset_x=offset_x,
            offset_z=offset_z,
            structure_width=structure_width,
            structure_depth=structure_depth,
        ):
            continue

        if is_path_related_token(row[site_x]):
            row[site_x] = GRASS_BLOCK
            erased += 1

    return erased


def erase_path_at_site(
    site_ground: list[list[str]],
    site_x: int,
    site_z: int,
    path_width: int,
    *,
    orientation: PathOrientation = DEFAULT_PATH_ORIENTATION,
    offset_x: int = 0,
    offset_z: int = 0,
    structure_width: int = 0,
    structure_depth: int = 0,
    trim_width: int = DEFAULT_TRIM_WIDTH,
) -> bool:
    """Erase all path/trim on the clicked row or column (per orientation).

    ``path_width`` and ``trim_width`` are accepted for API compatibility but are not used.
    Returns False if the anchor is on the structure footprint.
    """
    del path_width, trim_width

    if site_z < 0 or site_z >= len(site_ground):
        return False

    row = site_ground[site_z]

    if site_x < 0 or site_x >= len(row):
        return False

    if site_cell_in_structure_footprint(
        site_x,
        site_z,
        offset_x=offset_x,
        offset_z=offset_z,
        structure_width=structure_width,
        structure_depth=structure_depth,
    ):
        return False

    footprint = {
        "offset_x": offset_x,
        "offset_z": offset_z,
        "structure_width": structure_width,
        "structure_depth": structure_depth,
    }

    if orientation == "vertical":
        erased = _erase_all_path_cells_on_column(site_ground, site_x, **footprint)
    else:
        erased = _erase_all_path_cells_on_row(row, site_z, **footprint)

    return erased > 0


def clear_all_paths(site_ground: list[list[str]]) -> int:
    """Replace every painted path/trim cell with ``GRASS``. Returns cells cleared."""
    cleared = 0

    for row in site_ground:
        for index, token in enumerate(row):
            if is_path_related_token(token):
                row[index] = GRASS_BLOCK
                cleared += 1

    return cleared
