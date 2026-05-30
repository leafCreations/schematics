from dataclasses import dataclass

from helpers import grid as grid_utils
from helpers.context import SchematicContext

STAIR_LOCAL_X = 4
PATH_WIDTH = 3
TRIM_WIDTH = 1
LIGHTING_SPACING = 7
LIGHTING_START_OFFSET = 10


@dataclass(frozen=True)
class PathGeometry:
    stair_center_x: int
    path_start_z: int
    path_left: int
    path_right: int
    trim_left: int
    trim_right: int
    site_size: int

    def is_path_row(self, z: int) -> bool:
        return self.path_start_z <= z < self.site_size

    def is_on_path(self, x: int, z: int) -> bool:
        return self.is_path_row(z) and self.path_left <= x <= self.path_right

    def is_on_trim(self, x: int, z: int) -> bool:
        return (
            self.is_path_row(z)
            and self.trim_left <= x <= self.trim_right
            and not self.is_on_path(x, z)
        )

    def is_lighting_row(self, z: int) -> bool:
        if not self.is_path_row(z):
            return False

        relative_z = z - self.path_start_z

        return (
            relative_z >= LIGHTING_START_OFFSET
            and (relative_z - LIGHTING_START_OFFSET) % LIGHTING_SPACING == 0
        )

    def is_lighting_column(self, x: int) -> bool:
        return x == self.trim_left or x == self.trim_right


def get_path_geometry(ctx: SchematicContext) -> PathGeometry:
    offset_x = grid_utils.get_offset_x(ctx)
    offset_z = grid_utils.get_offset_z(ctx)
    structure_depth = grid_utils.get_structure_depth(ctx)
    site_size = grid_utils.get_site_size(ctx)

    stair_center_x = offset_x + STAIR_LOCAL_X
    path_start_z = offset_z + structure_depth

    path_left = stair_center_x - (PATH_WIDTH // 2)
    path_right = stair_center_x + (PATH_WIDTH // 2)
    trim_left = path_left - TRIM_WIDTH
    trim_right = path_right + TRIM_WIDTH

    return PathGeometry(
        stair_center_x=stair_center_x,
        path_start_z=path_start_z,
        path_left=path_left,
        path_right=path_right,
        trim_left=trim_left,
        trim_right=trim_right,
        site_size=site_size,
    )
