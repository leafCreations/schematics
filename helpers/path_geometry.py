from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from helpers import grid as grid_utils
from helpers.context import SchematicContext
from helpers.path_lighting import iter_lighting_fence_cells_from_ground
from helpers.path_strip import (
    DEFAULT_TRIM_WIDTH,
    DIRT_PATH_BLOCK,
    TRIM_BLOCK,
    PathOrientation,
    is_trim_token,
    resolve_path_orientation,
    resolve_path_variety_blocks,
    resolve_path_width,
    resolve_trim_block,
)

PATH_WIDTH = 3
TRIM_WIDTH = DEFAULT_TRIM_WIDTH
LIGHTING_SPACING = 7
LIGHTING_START_OFFSET = 10


@dataclass(frozen=True)
class PathGeometry:
    """Path corridor on the site grid for lighting and auto-generated strips."""

    orientation: PathOrientation
    path_center_x: int
    path_left: int
    path_right: int
    trim_left: int
    trim_right: int
    path_start_z: int
    path_end_z: int
    path_start_x: int
    path_end_x: int
    path_row_z: int
    site_width: int
    site_depth: int
    from_site_ground: bool = False
    lighting_site_ground: list[list[str]] | None = None
    trim_block: str = TRIM_BLOCK

    def is_path_row(self, z: int) -> bool:
        return self.path_start_z <= z <= self.path_end_z

    def is_on_path(self, x: int, z: int) -> bool:
        return self.is_path_row(z) and self.path_left <= x <= self.path_right

    def is_on_trim(self, x: int, z: int) -> bool:
        return (
            self.is_path_row(z)
            and self.trim_left <= x <= self.trim_right
            and not self.is_on_path(x, z)
        )

    def is_lighting_row(self, z: int) -> bool:
        """True when a horizontal-path corridor uses fence posts along this row index."""
        if self.orientation != "vertical":
            return False

        return z in self._lighting_indices(self.path_start_z, self.path_end_z)

    def is_lighting_column(self, x: int) -> bool:
        """True when a vertical-path corridor uses fence posts along this column index."""
        if self.orientation != "horizontal":
            return False

        return x in self._lighting_indices(self.path_start_x, self.path_end_x)

    def iter_lighting_fence_cells(
        self,
        site_ground: list[list[str]] | None = None,
    ) -> Iterator[tuple[int, int]]:
        """Yield site (x, z) cells for fence posts (torch sits above at y=1)."""
        ground = site_ground if site_ground is not None else self.lighting_site_ground

        if self.from_site_ground and ground is not None:
            yield from iter_lighting_fence_cells_from_ground(
                ground,
                trim_block=self.trim_block,
            )
            return

        seen: set[tuple[int, int]] = set()

        if self.orientation == "vertical":
            for z in self._lighting_indices(self.path_start_z, self.path_end_z):
                for x in (self.trim_left, self.trim_right):
                    if 0 <= x < self.site_width and 0 <= z < self.site_depth:
                        cell = (x, z)

                        if cell not in seen:
                            seen.add(cell)
                            yield cell
            return

        for _x in self._lighting_indices(self.path_start_x, self.path_end_x):
            for trim_x in (self.trim_left, self.trim_right):
                z = self.path_row_z

                if 0 <= trim_x < self.site_width and 0 <= z < self.site_depth:
                    cell = (trim_x, z)

                    if cell not in seen:
                        seen.add(cell)
                        yield cell

    def _lighting_indices(self, start: int, end: int) -> list[int]:
        if end < start:
            return []

        indices: list[int] = []
        z = start + LIGHTING_START_OFFSET

        while z <= end:
            indices.append(z)
            z += LIGHTING_SPACING

        return indices


def _scan_site_ground(
    site_ground: list[list[str]],
    *,
    trim_block: str = TRIM_BLOCK,
    variety_blocks: list[str] | None = None,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    path_cells: list[tuple[int, int]] = []
    trim_cells: list[tuple[int, int]] = []

    for site_z, row in enumerate(site_ground):
        for site_x, token in enumerate(row):
            if is_trim_token(token, trim_block=trim_block):
                trim_cells.append((site_x, site_z))
            elif token == DIRT_PATH_BLOCK or variety_blocks and token in variety_blocks:
                path_cells.append((site_x, site_z))

    return path_cells, trim_cells


def derive_path_geometry_from_ground(
    site_ground: list[list[str]],
    *,
    orientation: PathOrientation,
    path_width: int,
    trim_block: str = TRIM_BLOCK,
    variety_blocks: list[str] | None = None,
) -> PathGeometry | None:
    """Build path bounds from painted ``site_ground`` (editor brush strokes)."""
    path_cells, trim_cells = _scan_site_ground(
        site_ground,
        trim_block=trim_block,
        variety_blocks=variety_blocks,
    )

    if not path_cells and not trim_cells:
        return None

    site_depth = len(site_ground)
    site_width = len(site_ground[0]) if site_ground else 0
    path_xs = [x for x, _ in path_cells]
    path_zs = [z for _, z in path_cells]
    trim_xs = [x for x, _ in trim_cells]
    trim_zs = [z for _, z in trim_cells]

    if orientation == "vertical":
        path_left = min(path_xs) if path_xs else min(trim_xs, default=0)
        path_right = max(path_xs) if path_xs else max(trim_xs, default=0)

        if trim_xs:
            trim_left = min(trim_xs)
            trim_right = max(trim_xs)
        else:
            trim_left = path_left - TRIM_WIDTH
            trim_right = path_right + TRIM_WIDTH

        extent_z = path_zs + trim_zs
        path_start_z = min(extent_z)
        path_end_z = max(extent_z)
        path_start_x = path_left
        path_end_x = path_right
        path_row_z = path_start_z
        path_center_x = (path_left + path_right) // 2
    else:
        path_left = min(path_xs) if path_xs else min(trim_xs, default=0)
        path_right = max(path_xs) if path_xs else max(trim_xs, default=0)

        if trim_xs:
            trim_left = min(trim_xs)
            trim_right = max(trim_xs)
        else:
            trim_left = path_left - TRIM_WIDTH
            trim_right = path_right + TRIM_WIDTH

        extent_x = path_xs + trim_xs
        path_start_x = min(extent_x)
        path_end_x = max(extent_x)
        extent_z = path_zs + trim_zs
        path_row_z = min(path_zs) if path_zs else min(trim_zs, default=0)
        path_start_z = min(extent_z) if extent_z else path_row_z
        path_end_z = max(extent_z) if extent_z else path_row_z
        path_center_x = (path_left + path_right) // 2

    return PathGeometry(
        orientation=orientation,
        path_center_x=path_center_x,
        path_left=path_left,
        path_right=path_right,
        trim_left=trim_left,
        trim_right=trim_right,
        path_start_z=path_start_z,
        path_end_z=path_end_z,
        path_start_x=path_start_x,
        path_end_x=path_end_x,
        path_row_z=path_row_z,
        site_width=site_width,
        site_depth=site_depth,
        from_site_ground=True,
        lighting_site_ground=site_ground,
        trim_block=trim_block,
    )


def _default_path_geometry(ctx: SchematicContext, orientation: PathOrientation) -> PathGeometry:
    """Fallback path corridor when ``site_ground`` has no painted path/trim.

    Path starts at the south edge of the structure footprint and is centered on
    ``path_center_local_x`` (grid metadata). STAIRS in layer cells are not consulted.
    """
    offset_x = grid_utils.get_offset_x(ctx)
    offset_z = grid_utils.get_offset_z(ctx)
    structure_depth = grid_utils.get_structure_depth(ctx)
    site_width = grid_utils.get_site_width(ctx)
    site_depth = grid_utils.get_site_depth(ctx)
    path_width = resolve_path_width(ctx.grid)

    path_center_x = offset_x + grid_utils.get_path_center_local_x(ctx)
    path_start_z = offset_z + structure_depth
    path_left = path_center_x - (path_width // 2)
    path_right = path_left + path_width - 1
    trim_left = path_left - TRIM_WIDTH
    trim_right = path_right + TRIM_WIDTH

    return PathGeometry(
        orientation=orientation,
        path_center_x=path_center_x,
        path_left=path_left,
        path_right=path_right,
        trim_left=trim_left,
        trim_right=trim_right,
        path_start_z=path_start_z,
        path_end_z=site_depth - 1,
        path_start_x=0,
        path_end_x=site_width - 1,
        path_row_z=path_start_z,
        site_width=site_width,
        site_depth=site_depth,
        from_site_ground=False,
    )


def get_path_geometry(ctx: SchematicContext) -> PathGeometry:
    orientation = resolve_path_orientation(ctx.grid)

    if ctx.site_ground is not None:
        derived = derive_path_geometry_from_ground(
            ctx.site_ground,
            orientation=orientation,
            path_width=resolve_path_width(ctx.grid),
            trim_block=resolve_trim_block(ctx.grid),
            variety_blocks=resolve_path_variety_blocks(ctx.grid),
        )

        if derived is not None:
            return derived

    return _default_path_geometry(ctx, orientation)
