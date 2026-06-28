"""Tests for free-camera math in helpers/orbit_camera.py."""

from __future__ import annotations

import math

from helpers.block_picker import format_hud_block_label
from helpers.orbit_camera import (
    compass_facing_name,
    default_exterior_eye,
    dolly_along_forward,
    format_camera_hud_lines,
    forward_vector,
    grid_cell_from_world,
    move_along_look,
    move_on_plane,
    raycast_voxel,
    right_vector,
)


def test_forward_vector_horizontal_when_elevation_zero():
    fwd = forward_vector(0.7, 0.0)

    assert abs(fwd[1]) < 1e-9
    length = math.sqrt(fwd[0] ** 2 + fwd[1] ** 2 + fwd[2] ** 2)
    assert abs(length - 1.0) < 1e-9


def test_move_on_plane_strafe_and_forward():
    start = (10.0, 5.0, 10.0)
    azimuth = 0.0
    elevation = 0.0
    step = 2.0

    forward_pos = move_on_plane(start, azimuth, elevation, 1.0, 0.0, step)
    strafe_pos = move_on_plane(start, azimuth, elevation, 0.0, 1.0, step)

    assert forward_pos[1] == start[1]
    assert strafe_pos[1] == start[1]
    assert forward_pos != start
    assert strafe_pos != start
    assert forward_pos != strafe_pos
    assert forward_pos[2] < start[2]
    assert strafe_pos[0] > start[0]


def test_right_vector_points_east_when_facing_north():
    right = right_vector(0.0, 0.0)

    assert right[0] > 0.9
    assert abs(right[1]) < 1e-9
    assert abs(right[2]) < 1e-9


def test_default_exterior_eye_matches_legacy_orbit_offset():
    center = (1.0, 2.0, 3.0)
    radius = 4.0
    azimuth = 0.7
    elevation = 0.45
    distance = 12.0

    eye = default_exterior_eye(center, radius, azimuth, elevation, distance)
    cx, cy, cz = center
    dist = max(distance, radius * 1.8)
    expected = (
        cx + dist * math.cos(elevation) * math.sin(azimuth),
        cy + dist * math.sin(elevation),
        cz + dist * math.cos(elevation) * math.cos(azimuth),
    )

    assert eye == expected


def test_dolly_moves_along_forward():
    start = (0.0, 0.0, 0.0)
    azimuth = 0.0
    elevation = 0.0
    delta = 3.0

    end = dolly_along_forward(start, azimuth, elevation, delta)
    fwd = forward_vector(azimuth, elevation)

    assert abs(end[0] - fwd[0] * delta) < 1e-9
    assert abs(end[1] - fwd[1] * delta) < 1e-9
    assert abs(end[2] - fwd[2] * delta) < 1e-9


def test_move_along_look_follows_pitch_when_elevation_nonzero():
    start = (0.0, 10.0, 0.0)
    azimuth = 0.0
    elevation = 0.5
    step = 2.0

    end = move_along_look(start, azimuth, elevation, 1.0, step)
    fwd = forward_vector(azimuth, elevation)

    assert end[1] < start[1]
    assert abs(end[0] - (start[0] + fwd[0] * step)) < 1e-9
    assert abs(end[1] - (start[1] + fwd[1] * step)) < 1e-9
    assert abs(end[2] - (start[2] + fwd[2] * step)) < 1e-9


def test_right_vector_perpendicular_to_forward_on_horizontal_plane():
    azimuth = 1.2
    elevation = 0.3
    fwd = forward_vector(azimuth, elevation)
    right = right_vector(azimuth, elevation)

    dot = fwd[0] * right[0] + fwd[1] * right[1] + fwd[2] * right[2]
    assert abs(dot) < 0.15
    assert abs(right[1]) < 1e-9


def test_compass_facing_name_north_south_east_west():
    assert compass_facing_name(0.0, 0.0) == "North"
    assert compass_facing_name(math.pi, 0.0) == "South"
    assert compass_facing_name(-math.pi / 2, 0.0) == "East"
    assert compass_facing_name(math.pi / 2, 0.0) == "West"


def test_raycast_voxel_hits_first_occupied_cell():
    voxel_map = {(5, 3, 7): "COBBLESTONE"}
    origin = (5.5, 3.5, 6.5)
    direction = (0.0, 0.0, 1.0)

    hit = raycast_voxel(origin, direction, voxel_map)

    assert hit == ((5, 3, 7), "COBBLESTONE")


def test_raycast_voxel_miss_returns_none():
    voxel_map = {(5, 3, 7): "COBBLESTONE"}
    origin = (5.5, 3.5, 6.5)
    direction = (0.0, 0.0, -1.0)

    assert raycast_voxel(origin, direction, voxel_map) is None


def test_grid_cell_from_world_applies_offsets():
    assert grid_cell_from_world((12, 3, 9), offset_x=5, offset_z=1) == (7, 3, 8)


def test_format_hud_block_label_default_name():
    assert format_hud_block_label("COBBLESTONE", mode="name") == "Cobblestone"


def test_format_hud_block_label_includes_material_for_log():
    assert format_hud_block_label("LOG:oak", mode="name") == "Oak Log"
    assert format_hud_block_label("LOG:spruce", mode="name") == "Spruce Log"


def test_format_hud_block_label_id_mode():
    label = format_hud_block_label("minecraft:cobblestone", mode="id")
    assert label == "minecraft:cobblestone"


def test_format_camera_hud_lines_includes_none_on_miss():
    lines = format_camera_hud_lines(
        azimuth=0.0,
        elevation=0.0,
        position=(1.0, 2.0, 3.0),
        offset_x=0,
        offset_z=0,
        voxel_map={},
    )

    assert lines[0].startswith("Facing:")
    assert lines[1] == "Position: X 1.0 / Y 2.0 / Z 3.0"
    assert lines[2] == "Looking at: (none)"


def test_format_camera_hud_lines_uses_slash_cell_coords():
    lines = format_camera_hud_lines(
        azimuth=math.pi,
        elevation=0.0,
        position=(5.5, 3.5, 6.5),
        offset_x=0,
        offset_z=0,
        voxel_map={(5, 3, 7): "LOG:oak"},
        block_label_fn=lambda _token: "Oak Log",
    )

    assert lines[2] == "Looking at: Oak Log (cell: X 5 / Y 3 / Z 7)"
