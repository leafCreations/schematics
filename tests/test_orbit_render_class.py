"""Tests for helpers.orbit_render_class — agent-facing orbit dispatch taxonomy."""

from helpers.orbit_render_class import orbit_render_class


def test_cobblestone_is_solid_cube():
    assert orbit_render_class("minecraft:cobblestone") == "solid_cube"


def test_torch_is_block_model():
    assert orbit_render_class("TORCH") == "block_model"
    assert orbit_render_class("TORCH@north#wall") == "block_model"


def test_slab_is_partial_box():
    assert orbit_render_class("SLAB:oak") == "partial_box"


def test_bed_is_attachable_box():
    assert orbit_render_class("BED:blue@north#head") == "attachable_box"
    assert orbit_render_class("BED:blue@north#foot") == "attachable_box"


def test_copper_lantern_exposed_is_block_model():
    assert orbit_render_class("COPPER_LANTERN#exposed") == "block_model"


def test_chest_is_attachable_box():
    assert orbit_render_class("CHEST@north#single") == "attachable_box"
    assert orbit_render_class("CHEST@west#left") == "attachable_box"


def test_door_is_attachable_box():
    assert orbit_render_class("DOOR:oak@north#lower") == "attachable_box"


def test_fence_is_partial_box():
    assert orbit_render_class("FENCE:oak") == "partial_box"


def test_trapdoor_closed_is_block_model():
    assert orbit_render_class("TRAPDOOR:oak@north;open=false") == "block_model"


def test_trapdoor_open_is_block_model():
    assert orbit_render_class("TRAPDOOR:oak@north;open=true") == "block_model"
