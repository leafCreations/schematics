"""Site ground-layer grid (y=-1 landscaping) for editor and renders."""

from __future__ import annotations

from helpers.grid_cells import resize_cells

GRASS_BLOCK = "GRASS"


def create_grass_site_ground(site_width: int, site_depth: int) -> list[list[str]]:
    if site_width < 1 or site_depth < 1:
        raise ValueError("Site width and depth must be at least 1")

    return [["GRASS" for _ in range(site_width)] for _ in range(site_depth)]


def resize_site_ground(
    site_ground: list[list[str]],
    site_width: int,
    site_depth: int,
) -> list[list[str]]:
    return resize_cells(site_ground, site_width, site_depth)


def validate_site_ground(
    site_ground: object,
    site_width: int,
    site_depth: int,
    *,
    path: str = "site_ground",
) -> list[list[str]]:
    if not isinstance(site_ground, list):
        raise ValueError(f"{path} must be a list of rows")

    if len(site_ground) != site_depth:
        raise ValueError(
            f"{path} has {len(site_ground)} rows; expected {site_depth} for site depth",
        )

    validated: list[list[str]] = []

    for z, row in enumerate(site_ground):
        if not isinstance(row, list):
            raise ValueError(f"{path} row {z} must be a list")

        if len(row) != site_width:
            raise ValueError(
                f"{path} row {z} has {len(row)} columns; expected {site_width}",
            )

        validated.append([str(cell) for cell in row])

    return validated


def ensure_site_ground(
    site_ground: list[list[str]] | None,
    site_width: int,
    site_depth: int,
) -> list[list[str]]:
    if site_ground is None:
        return create_grass_site_ground(site_width, site_depth)

    return validate_site_ground(site_ground, site_width, site_depth)
