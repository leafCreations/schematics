"""Free-camera math for Viewer 3D orbit preview (no OpenGL dependency)."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping

from helpers.block_picker import format_hud_block_label

_WORLD_UP = (0.0, 1.0, 0.0)


def _normalize(x: float, y: float, z: float) -> tuple[float, float, float]:
    length = math.sqrt(x * x + y * y + z * z)
    if length < 1e-9:
        return (0.0, 0.0, 0.0)
    return (x / length, y / length, z / length)


def forward_vector(azimuth: float, elevation: float) -> tuple[float, float, float]:
    """Unit look direction from azimuth (yaw) and elevation (pitch)."""
    x = -math.cos(elevation) * math.sin(azimuth)
    y = -math.sin(elevation)
    z = -math.cos(elevation) * math.cos(azimuth)
    return _normalize(x, y, z)


def right_vector(azimuth: float, elevation: float) -> tuple[float, float, float]:
    """Unit camera-right vector (cross(forward, world +Y))."""
    fwd_x, fwd_y, fwd_z = forward_vector(azimuth, elevation)
    rx = fwd_y * _WORLD_UP[2] - fwd_z * _WORLD_UP[1]
    ry = fwd_z * _WORLD_UP[0] - fwd_x * _WORLD_UP[2]
    rz = fwd_x * _WORLD_UP[1] - fwd_y * _WORLD_UP[0]
    return _normalize(rx, ry, rz)


def _horizontal_forward(azimuth: float, elevation: float) -> tuple[float, float, float]:
    fwd_x, _fwd_y, fwd_z = forward_vector(azimuth, elevation)
    return _normalize(fwd_x, 0.0, fwd_z)


def default_exterior_eye(
    bounds_center: tuple[float, float, float],
    bounds_radius: float,
    azimuth: float,
    elevation: float,
    distance: float,
) -> tuple[float, float, float]:
    """Eye position matching legacy orbit-around-center exterior framing."""
    cx, cy, cz = bounds_center
    radius = max(bounds_radius, 1.0)
    dist = max(distance, radius * 1.8)
    eye_x = cx + dist * math.cos(elevation) * math.sin(azimuth)
    eye_y = cy + dist * math.sin(elevation)
    eye_z = cz + dist * math.cos(elevation) * math.cos(azimuth)
    return (eye_x, eye_y, eye_z)


def move_on_plane(
    position: tuple[float, float, float],
    azimuth: float,
    elevation: float,
    forward_delta: float,
    strafe_delta: float,
    step: float,
) -> tuple[float, float, float]:
    """Translate on the horizontal plane relative to view facing."""
    h_fwd = _horizontal_forward(azimuth, elevation)
    right = right_vector(azimuth, elevation)
    x, y, z = position
    x += (h_fwd[0] * forward_delta + right[0] * strafe_delta) * step
    z += (h_fwd[2] * forward_delta + right[2] * strafe_delta) * step
    return (x, y, z)


def move_along_look(
    position: tuple[float, float, float],
    azimuth: float,
    elevation: float,
    forward_delta: float,
    step: float,
) -> tuple[float, float, float]:
    """Translate along the full look vector (keyboard W/S forward/back)."""
    fwd = forward_vector(azimuth, elevation)
    scale = forward_delta * step
    x, y, z = position
    return (x + fwd[0] * scale, y + fwd[1] * scale, z + fwd[2] * scale)


def dolly_along_forward(
    position: tuple[float, float, float],
    azimuth: float,
    elevation: float,
    delta: float,
) -> tuple[float, float, float]:
    """Move eye position along the full look vector."""
    return move_along_look(position, azimuth, elevation, 1.0, delta)


def compass_facing_name(azimuth: float, elevation: float) -> str:
    """Return North/South/East/West from the horizontal look direction (+X east, +Z south)."""
    fwd_x, _, fwd_z = forward_vector(azimuth, elevation)
    if abs(fwd_x) >= abs(fwd_z):
        return "East" if fwd_x > 0 else "West"
    return "South" if fwd_z > 0 else "North"


def grid_cell_from_world(
    world: tuple[int, int, int],
    *,
    offset_x: int,
    offset_z: int,
) -> tuple[int, int, int]:
    """Convert orbit world voxel coordinates to structure grid indices."""
    wx, wy, wz = world
    return (wx - offset_x, wy, wz - offset_z)


def raycast_voxel(
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
    voxel_map: Mapping[tuple[int, int, int], str],
    *,
    max_distance: float = 512.0,
) -> tuple[tuple[int, int, int], str] | None:
    """Return the first occupied voxel along a ray using 3D grid traversal."""
    if not voxel_map:
        return None

    ox, oy, oz = origin
    dx, dy, dz = direction
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-9:
        return None
    dx /= length
    dy /= length
    dz /= length

    x = int(math.floor(ox))
    y = int(math.floor(oy))
    z = int(math.floor(oz))

    step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
    step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
    step_z = 1 if dz > 0 else (-1 if dz < 0 else 0)

    if dx > 0:
        t_max_x = (x + 1 - ox) / dx
    elif dx < 0:
        t_max_x = (ox - x) / -dx
    else:
        t_max_x = float("inf")

    if dy > 0:
        t_max_y = (y + 1 - oy) / dy
    elif dy < 0:
        t_max_y = (oy - y) / -dy
    else:
        t_max_y = float("inf")

    if dz > 0:
        t_max_z = (z + 1 - oz) / dz
    elif dz < 0:
        t_max_z = (oz - z) / -dz
    else:
        t_max_z = float("inf")

    t_delta_x = abs(1.0 / dx) if dx else float("inf")
    t_delta_y = abs(1.0 / dy) if dy else float("inf")
    t_delta_z = abs(1.0 / dz) if dz else float("inf")

    distance = 0.0
    while distance <= max_distance:
        hit = voxel_map.get((x, y, z))
        if hit is not None:
            return ((x, y, z), hit)

        if t_max_x < t_max_y:
            if t_max_x < t_max_z:
                x += step_x
                distance = t_max_x
                t_max_x += t_delta_x
            else:
                z += step_z
                distance = t_max_z
                t_max_z += t_delta_z
        elif t_max_y < t_max_z:
            y += step_y
            distance = t_max_y
            t_max_y += t_delta_y
        else:
            z += step_z
            distance = t_max_z
            t_max_z += t_delta_z

    return None


def format_camera_hud_lines(
    *,
    azimuth: float,
    elevation: float,
    position: tuple[float, float, float],
    offset_x: int,
    offset_z: int,
    voxel_map: Mapping[tuple[int, int, int], str],
    block_label_fn: Callable[[str], str] | None = None,
) -> tuple[str, str, str]:
    """Build the three HUD lines for Facing, Position, and Looking at."""
    label_fn = block_label_fn or (lambda token: format_hud_block_label(token, mode="name"))
    px, py, pz = position
    facing_line = f"Facing: {compass_facing_name(azimuth, elevation)}"
    position_line = f"Position: X {px:.1f} / Y {py:.1f} / Z {pz:.1f}"

    hit = raycast_voxel(position, forward_vector(azimuth, elevation), voxel_map)
    if hit is None:
        looking_line = "Looking at: (none)"
    else:
        world, token = hit
        gx, gy, gz = grid_cell_from_world(world, offset_x=offset_x, offset_z=offset_z)
        cell_coords = f"X {gx} / Y {gy} / Z {gz}"
        looking_line = f"Looking at: {label_fn(token)} (cell: {cell_coords})"

    return facing_line, position_line, looking_line
