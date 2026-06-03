"""Fence/torch placement along painted path trim runs."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator

from helpers.path_strip import TRIM_BLOCK, is_trim_token

LIGHTING_SPACING = 7
LIGHTING_START_OFFSET = 10
MIN_TRIM_RUN = 8


def _contiguous_runs(sorted_coords: list[int]) -> list[tuple[int, int]]:
    if not sorted_coords:
        return []

    runs: list[tuple[int, int]] = []
    run_start = sorted_coords[0]
    run_end = run_start

    for coord in sorted_coords[1:]:
        if coord == run_end + 1:
            run_end = coord
            continue

        runs.append((run_start, run_end))
        run_start = run_end = coord

    runs.append((run_start, run_end))
    return runs


def _lighting_coords(start: int, end: int) -> list[int]:
    if end < start:
        return []

    coords: list[int] = []
    value = start + LIGHTING_START_OFFSET

    while value <= end:
        coords.append(value)
        value += LIGHTING_SPACING

    return coords


def iter_lighting_fence_cells_from_ground(
    site_ground: list[list[str]],
    *,
    trim_block: str = TRIM_BLOCK,
) -> Iterator[tuple[int, int]]:
    """Place fence posts on configured trim along long horizontal and vertical runs.

    Scans contiguous trim cells per grid row and column (``trim_block`` only, not
    path-variety blocks in the center band). First post at run start + 10, then
    every 7 cells; runs shorter than 8 trim cells are skipped.
    """
    trim_by_x: dict[int, set[int]] = defaultdict(set)
    trim_by_z: dict[int, set[int]] = defaultdict(set)

    for site_z, row in enumerate(site_ground):
        for site_x, token in enumerate(row):
            if is_trim_token(token, trim_block=trim_block):
                trim_by_x[site_x].add(site_z)
                trim_by_z[site_z].add(site_x)

    seen: set[tuple[int, int]] = set()

    for site_x, site_zs in trim_by_x.items():
        for run_start, run_end in _contiguous_runs(sorted(site_zs)):
            for site_z in _lighting_coords(run_start, run_end):
                cell = (site_x, site_z)

                if cell not in seen:
                    seen.add(cell)
                    yield cell

    for site_z, site_xs in trim_by_z.items():
        for run_start, run_end in _contiguous_runs(sorted(site_xs)):
            for site_x in _lighting_coords(run_start, run_end):
                cell = (site_x, site_z)

                if cell not in seen:
                    seen.add(cell)
                    yield cell
