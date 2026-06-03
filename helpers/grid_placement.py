"""Site grid placement: map structure footprint to offset_x/offset_z on a site."""

from __future__ import annotations

from typing import Literal

Placement = Literal[
    "top_left",
    "top_center",
    "top_right",
    "middle_left",
    "center",
    "middle_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
]

PLACEMENTS: tuple[Placement, ...] = (
    "top_left",
    "top_center",
    "top_right",
    "middle_left",
    "center",
    "middle_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
)

PLACEMENT_LABELS: dict[Placement, str] = {
    "top_left": "Top left",
    "top_center": "Top center",
    "top_right": "Top right",
    "middle_left": "Middle left",
    "center": "Center",
    "middle_right": "Middle right",
    "bottom_left": "Bottom left",
    "bottom_center": "Bottom center",
    "bottom_right": "Bottom right",
}

DEFAULT_PLACEMENT: Placement = "center"


def site_cell_in_structure_footprint(
    site_x: int,
    site_z: int,
    *,
    offset_x: int,
    offset_z: int,
    structure_width: int,
    structure_depth: int,
) -> bool:
    """True when site coordinates fall inside the structure layer bounding box."""
    local_x = site_x - offset_x
    local_z = site_z - offset_z
    return 0 <= local_x < structure_width and 0 <= local_z < structure_depth


def structure_dimensions_from_layers(layers: list[dict]) -> tuple[int, int]:
    """Return (width, depth) in blocks from layer cell grids."""
    width = 1
    depth = 1

    for layer in layers:
        cells = layer.get("cells", [])

        if not cells:
            continue

        depth = max(depth, len(cells))
        width = max(width, max((len(row) for row in cells), default=1))

    return width, depth


def max_offsets(
    site_width: int,
    site_depth: int,
    structure_width: int,
    structure_depth: int,
) -> tuple[int, int]:
    """Return the largest valid offset_x and offset_z."""
    return site_width - structure_width, site_depth - structure_depth


def offsets_for_placement(
    placement: Placement,
    site_width: int,
    site_depth: int,
    structure_width: int,
    structure_depth: int,
) -> tuple[int, int]:
    """Map a named anchor to offset_x/offset_z (north-west corner of structure)."""
    max_x, max_z = max_offsets(site_width, site_depth, structure_width, structure_depth)

    if max_x < 0 or max_z < 0:
        raise ValueError(
            f"Structure {structure_width}x{structure_depth} does not fit in site "
            f"{site_width}x{site_depth}",
        )

    center_x = max_x // 2
    center_z = max_z // 2

    horizontal = {
        "left": 0,
        "center": center_x,
        "right": max_x,
    }
    vertical = {
        "top": 0,
        "middle": center_z,
        "bottom": max_z,
    }

    if placement == "center":
        return center_x, center_z

    row, column = placement.split("_", 1)
    return horizontal[column], vertical[row]


def infer_placement(
    offset_x: int,
    offset_z: int,
    site_width: int,
    site_depth: int,
    structure_width: int,
    structure_depth: int,
) -> Placement:
    """Pick the closest named anchor for existing offsets."""
    best: Placement = DEFAULT_PLACEMENT
    best_distance = float("inf")

    for placement in PLACEMENTS:
        anchor_x, anchor_z = offsets_for_placement(
            placement,
            site_width,
            site_depth,
            structure_width,
            structure_depth,
        )
        distance = abs(anchor_x - offset_x) + abs(anchor_z - offset_z)

        if distance < best_distance:
            best_distance = distance
            best = placement

    return best


def structure_fits_site(
    site_width: int,
    site_depth: int,
    structure_width: int,
    structure_depth: int,
    offset_x: int,
    offset_z: int,
) -> bool:
    return (
        offset_x >= 0
        and offset_z >= 0
        and offset_x + structure_width <= site_width
        and offset_z + structure_depth <= site_depth
    )


def apply_placement_to_grid(
    grid: dict,
    *,
    placement: Placement,
    site_width: int,
    site_depth: int,
    structure_width: int,
    structure_depth: int,
) -> dict:
    """Update grid dict with site dimensions, placement, and derived offsets."""
    offset_x, offset_z = offsets_for_placement(
        placement,
        site_width,
        site_depth,
        structure_width,
        structure_depth,
    )

    updated = dict(grid)
    updated["site_width"] = site_width
    updated["site_depth"] = site_depth
    updated.pop("site_size", None)
    updated["placement"] = placement
    updated["offset_x"] = offset_x
    updated["offset_z"] = offset_z
    return updated


def minimum_site_dimensions(structure_width: int, structure_depth: int) -> tuple[int, int]:
    return max(structure_width, 1), max(structure_depth, 1)


def structure_exceeds_site(
    structure_width: int,
    structure_depth: int,
    site_width: int,
    site_depth: int,
) -> bool:
    return structure_width > site_width or structure_depth > site_depth


def structure_site_size_error(
    structure_width: int,
    structure_depth: int,
    site_width: int,
    site_depth: int,
) -> str | None:
    if not structure_exceeds_site(
        structure_width,
        structure_depth,
        site_width,
        site_depth,
    ):
        return None

    return (
        f"Structure {structure_width}×{structure_depth} cannot be larger than "
        f"site {site_width}×{site_depth}."
    )


def clamp_grid_offsets_for_structure(
    grid: dict,
    *,
    structure_width: int,
    structure_depth: int,
) -> dict:
    """Keep offsets valid after the structure footprint changes size."""
    from helpers.grid import resolve_site_dimensions

    site_width, site_depth = resolve_site_dimensions(grid)
    offset_x = max(0, min(int(grid.get("offset_x", 0)), site_width - structure_width))
    offset_z = max(0, min(int(grid.get("offset_z", 0)), site_depth - structure_depth))

    updated = dict(grid)
    updated["offset_x"] = offset_x
    updated["offset_z"] = offset_z
    updated["placement"] = infer_placement(
        offset_x,
        offset_z,
        site_width,
        site_depth,
        structure_width,
        structure_depth,
    )
    return updated


def nudge_structure_offset(
    grid: dict,
    *,
    delta_x: int,
    delta_z: int,
    structure_width: int,
    structure_depth: int,
) -> dict | None:
    """Shift ``offset_x`` / ``offset_z`` by one or more blocks if the structure still fits."""
    if delta_x == 0 and delta_z == 0:
        return dict(grid)

    from helpers.grid import resolve_site_dimensions

    site_width, site_depth = resolve_site_dimensions(grid)

    offset_x = int(grid.get("offset_x", 0)) + delta_x
    offset_z = int(grid.get("offset_z", 0)) + delta_z

    if not structure_fits_site(
        site_width,
        site_depth,
        structure_width,
        structure_depth,
        offset_x,
        offset_z,
    ):
        return None

    updated = dict(grid)
    updated["offset_x"] = offset_x
    updated["offset_z"] = offset_z
    updated["placement"] = infer_placement(
        offset_x,
        offset_z,
        site_width,
        site_depth,
        structure_width,
        structure_depth,
    )
    return updated
