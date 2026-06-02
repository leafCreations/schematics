from helpers.block_picker import (
    PickerEntry,
    cell_token,
    enumerate_token_materials,
    format_entry_label,
    list_palettes,
    picker_entry_for_block_id,
    picker_entry_for_token,
    resolve_palette,
)
from registries.loader import BLOCK_PALETTES


def test_enumerate_token_materials_from_catalog():
    materials = enumerate_token_materials("minecraft:{material}_planks")

    assert "oak" in materials
    assert "spruce" in materials
    assert materials == tuple(sorted(materials))


def test_enumerate_handles_color_placeholder():
    materials = enumerate_token_materials("minecraft:{color}_bed")

    assert "red" in materials
    assert "blue" in materials


def test_enumerate_returns_empty_for_static_block():
    assert enumerate_token_materials("minecraft:furnace") == ()
    assert enumerate_token_materials(None) == ()


def test_picker_entry_for_templated_token():
    entry = picker_entry_for_token("PLANKS")

    assert entry is not None
    assert entry.requires_material is True
    assert entry.material_field == "material"
    assert "oak" in entry.materials
    assert entry.behavior == "solid"


def test_picker_entry_for_static_token():
    entry = picker_entry_for_token("FURNACE")

    assert entry is not None
    assert entry.requires_material is False
    assert entry.materials == ()
    assert entry.label == "Furnace"
    assert entry.requires_direction is True


def test_picker_entry_for_unknown_token_returns_none():
    assert picker_entry_for_token("NOT_A_TOKEN") is None


def test_picker_entry_for_block_id():
    entry = picker_entry_for_block_id("minecraft:stone")

    assert entry.is_catalog_block is True
    assert entry.token == "minecraft:stone"
    assert entry.label == "Stone"
    assert entry.behavior == "solid"


def test_cell_token_for_material_and_catalog():
    planks = picker_entry_for_token("PLANKS")
    assert cell_token(planks, "spruce") == "PLANKS:spruce"
    assert cell_token(planks) == "PLANKS:oak"

    stone = picker_entry_for_block_id("minecraft:stone")
    assert cell_token(stone) == "minecraft:stone"

    furnace = picker_entry_for_token("FURNACE")
    assert cell_token(furnace) == "FURNACE"


def test_cell_token_includes_direction_and_variant():
    stairs = picker_entry_for_token("STAIRS")
    assert cell_token(stairs, "oak", direction="north") == "STAIRS:oak@north"
    assert (
        cell_token(stairs, "oak", direction="south", variant="outer_left")
        == "STAIRS:oak@south#outer_left"
    )

    cobblestone = picker_entry_for_token("COBBLESTONE")
    assert cell_token(cobblestone, variant="mossy") == "COBBLESTONE#mossy"

    door = picker_entry_for_token("DOOR")
    assert cell_token(door, "oak", direction="west") == "DOOR:oak@west"


def test_format_entry_label_uses_catalog():
    planks = picker_entry_for_token("PLANKS")

    assert format_entry_label(planks, "spruce") == "Spruce Planks"


def test_resolve_palette_includes_tokens_and_blocks():
    palette = resolve_palette("terrain")

    assert palette is not None
    assert palette.label == "Terrain"

    tokens = {e.token for e in palette.entries if not e.is_catalog_block}
    catalog_blocks = {e.token for e in palette.entries if e.is_catalog_block}

    assert "GRASS" in tokens
    assert "minecraft:stone" in catalog_blocks


def test_resolve_palette_unknown_returns_none():
    assert resolve_palette("does_not_exist") is None


def test_list_palettes_covers_all():
    palettes = list_palettes()

    assert {p.name for p in palettes} == set(BLOCK_PALETTES)
    assert all(isinstance(e, PickerEntry) for p in palettes for e in p.entries)
