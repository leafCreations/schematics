from helpers.block_picker import (
    PickerEntry,
    cell_positions_with_same_block_type,
    cell_token,
    entry_matches_search,
    enumerate_token_materials,
    format_entry_label,
    homogeneous_picker_entry_for_positions,
    list_palettes,
    picker_entry_for_block_id,
    picker_entry_for_cell,
    picker_entry_for_token,
    resolve_palette,
    search_picker_entries,
)
from registries.loader import BLOCK_PALETTES
from tests.palette_helpers import terrain_section_entry_counts


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
    assert entry.label == "Planks"
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

    cobblestone = next(
        entry
        for entry in resolve_palette("terrain").entries
        if entry.token == "minecraft:cobblestone"
    )
    assert cell_token(cobblestone, variant="mossy") == "minecraft:mossy_cobblestone"

    door = picker_entry_for_token("DOOR")
    assert door.variants == ("lower", "upper")
    assert cell_token(door, "oak", direction="west") == "DOOR:oak@west"
    assert cell_token(door, "oak", direction="west", variant="upper") == "DOOR:oak@west#upper"

    bed = picker_entry_for_token("BED")
    assert bed is not None
    assert bed.label == "Bed"
    assert bed.variants == ("head", "foot")
    assert cell_token(bed, "blue", direction="north", variant="head") == "BED:blue@north#head"
    assert cell_token(bed, "blue", direction="north", variant="foot") == "BED:blue@north#foot"


def test_cell_token_includes_block_states():
    lantern = picker_entry_for_token("LANTERN")

    assert lantern is not None
    assert cell_token(lantern, states=(("hanging", True),)) == "LANTERN;hanging=true"

    trapdoor = picker_entry_for_token("TRAPDOOR")
    assert trapdoor is not None
    assert (
        cell_token(trapdoor, "oak", direction="north", states=(("open", True),))
        == "TRAPDOOR:oak@north;open=true"
    )
    assert (
        cell_token(trapdoor, "oak", direction="north", states=(("open", False),))
        == "TRAPDOOR:oak@north;open=false"
    )

    campfire = picker_entry_for_block_id("minecraft:campfire", palette="lighting")
    assert campfire.requires_direction is True
    assert campfire.behavior == "campfire"
    assert (
        cell_token(campfire, direction="east", states=(("lit", False),))
        == "minecraft:campfire@east;lit=false"
    )


def test_cell_token_includes_optional_variant_without_requires_variant():
    lantern = picker_entry_for_token("LANTERN")

    assert lantern is not None
    assert lantern.requires_variant is False
    assert lantern.variants == ("soul",)
    assert cell_token(lantern, variant="soul") == "LANTERN#soul"


def test_picker_entry_for_cell_semantic_token():
    entry = picker_entry_for_cell("LANTERN#soul")

    assert entry is not None
    assert entry.token == "LANTERN"
    assert entry.palette == "lighting"


def test_picker_entry_for_cell_catalog_block():
    entry = picker_entry_for_cell("minecraft:stone")

    assert entry is not None
    assert entry.is_catalog_block is True
    assert entry.token == "minecraft:stone"


def test_picker_entry_for_cell_empty_returns_none():
    assert picker_entry_for_cell(".") is None


def test_homogeneous_picker_entry_same_planks_materials():
    cells = [
        ["PLANKS:oak", "PLANKS:spruce"],
        [".", "PLANKS:birch"],
    ]
    entry = homogeneous_picker_entry_for_positions(cells, [(0, 0), (0, 1), (1, 1)])

    assert entry is not None
    assert entry.token == "PLANKS"


def test_homogeneous_picker_entry_rejects_mixed_types():
    cells = [["PLANKS:oak", "STAIRS:oak@north"]]
    assert homogeneous_picker_entry_for_positions(cells, [(0, 0), (0, 1)]) is None


def test_homogeneous_picker_entry_rejects_empty_cells():
    cells = [["PLANKS:oak", "."]]
    assert homogeneous_picker_entry_for_positions(cells, [(0, 0), (0, 1)]) is None


def test_cell_positions_with_same_block_type_registry_materials():
    cells = [
        ["PLANKS:oak", "PLANKS:spruce"],
        [".", "PLANKS:birch"],
    ]
    positions = cell_positions_with_same_block_type(cells, "PLANKS:oak")

    assert set(positions) == {(0, 0), (0, 1), (1, 1)}


def test_cell_positions_with_same_block_type_empty_reference():
    assert cell_positions_with_same_block_type([["PLANKS:oak"]], ".") == []


def test_cell_positions_with_same_block_type_variant_not_matched():
    cells = [["COBBLESTONE", "COBBLESTONE#mossy"], ["COBBLESTONE", "."]]
    positions = cell_positions_with_same_block_type(cells, "COBBLESTONE")

    assert set(positions) == {(0, 0), (1, 0)}


def test_cell_positions_with_same_block_type_variant_matches_own_variant():
    cells = [["COBBLESTONE", "COBBLESTONE#mossy"], ["COBBLESTONE#mossy", "."]]
    positions = cell_positions_with_same_block_type(cells, "COBBLESTONE#mossy")

    assert set(positions) == {(0, 1), (1, 0)}


def test_cell_positions_with_same_block_type_legacy_and_catalog_equivalent():
    cells = [["COBBLESTONE", "minecraft:cobblestone"], ["GRASS", "."]]
    positions = cell_positions_with_same_block_type(cells, "minecraft:cobblestone")

    assert set(positions) == {(0, 0), (0, 1)}


def test_cell_positions_with_same_block_type_exact_token_fallback():
    cells = [["CUSTOM:1", "CUSTOM:2"], ["CUSTOM:1", "."]]
    positions = cell_positions_with_same_block_type(cells, "CUSTOM:1")

    assert set(positions) == {(0, 0), (1, 0)}


def test_cell_token_copper_lantern_variants():
    copper = picker_entry_for_token("COPPER_LANTERN")

    assert copper is not None
    assert cell_token(copper, variant="exposed") == "COPPER_LANTERN#exposed"
    assert cell_token(copper, variant="waxed_oxidized") == "COPPER_LANTERN#waxed_oxidized"


def test_format_entry_label_uses_catalog():
    planks = picker_entry_for_token("PLANKS")

    assert format_entry_label(planks, "spruce") == "Spruce Planks"


def test_format_entry_label_uses_stem_for_nether_logs():
    log = picker_entry_for_token("LOG")

    assert log is not None
    assert format_entry_label(log, "crimson") == "Crimson Stem"
    assert format_entry_label(log, "warped") == "Warped Stem"


def test_resolve_palette_includes_catalog_terrain_blocks():
    palette = resolve_palette("terrain")

    assert palette is not None
    assert palette.label == "Terrain"
    assert palette.sections == ("overworld", "nether", "end")

    tokens = {e.token for e in palette.entries if not e.is_catalog_block}
    catalog_blocks = {e.token for e in palette.entries if e.is_catalog_block}

    assert tokens == set()
    assert "minecraft:grass_block" in catalog_blocks
    assert "minecraft:stone" in catalog_blocks
    assert "minecraft:mossy_cobblestone" not in catalog_blocks

    cobblestone = next(entry for entry in palette.entries if entry.token == "minecraft:cobblestone")
    assert cobblestone.section == "overworld"
    assert cobblestone.variants == ("mossy",)
    assert cobblestone.variant_blocks == (("mossy", "minecraft:mossy_cobblestone"),)


def test_resolve_palette_terrain_sections_have_entries_per_dimension():
    palette = resolve_palette("terrain")
    assert palette is not None

    section_counts = terrain_section_entry_counts()

    assert section_counts.keys() == {"overworld", "nether", "end"}
    assert all(count > 0 for count in section_counts.values())
    assert sum(section_counts.values()) == len(palette.entries)

    for entry in palette.entries:
        assert entry.section in section_counts


def test_cell_token_for_catalog_terrain_variant():
    palette = resolve_palette("terrain")
    assert palette is not None

    cobblestone = next(entry for entry in palette.entries if entry.token == "minecraft:cobblestone")

    assert cell_token(cobblestone) == "minecraft:cobblestone"
    assert cell_token(cobblestone, variant="mossy") == "minecraft:mossy_cobblestone"


def test_picker_entry_for_cell_resolves_catalog_variant_block():
    entry = picker_entry_for_cell("minecraft:mossy_cobblestone")

    assert entry is not None
    assert entry.token == "minecraft:cobblestone"
    assert entry.is_catalog_block is True


def test_entry_matches_search_by_label_and_token():
    slab = picker_entry_for_token("SLAB")
    assert slab is not None

    assert entry_matches_search(slab, "slab")
    assert entry_matches_search(slab, "SLAB")
    assert not entry_matches_search(slab, "stairs")


def test_entry_matches_search_by_material():
    slab = picker_entry_for_token("SLAB")
    assert slab is not None

    assert entry_matches_search(slab, "oak")
    assert not entry_matches_search(slab, "zzznotablock")


def test_entry_matches_search_by_catalog_variant_block():
    palette = resolve_palette("terrain")
    assert palette is not None

    stone = next(entry for entry in palette.entries if entry.token == "minecraft:stone")
    cobblestone = next(entry for entry in palette.entries if entry.token == "minecraft:cobblestone")

    assert entry_matches_search(stone, "smooth stone")
    assert entry_matches_search(stone, "smooth_stone")
    assert entry_matches_search(cobblestone, "mossy")
    assert entry_matches_search(cobblestone, "mossy_cobblestone")
    assert not entry_matches_search(stone, "dirt")


def test_search_picker_entries_across_palettes():
    palettes = list_palettes()
    results = search_picker_entries(palettes, "cobblestone")
    tokens = {entry.token for entry in results}

    assert "minecraft:cobblestone" in tokens
    assert any(entry.palette == "building" for entry in results)
    assert any(entry.palette == "terrain" for entry in results)


def test_resolve_palette_unknown_returns_none():
    assert resolve_palette("does_not_exist") is None


def test_list_palettes_covers_all():
    palettes = list_palettes()

    assert {p.name for p in palettes} == set(BLOCK_PALETTES)
    assert all(isinstance(e, PickerEntry) for p in palettes for e in p.entries)
