import shutil
from collections.abc import Iterator

from amulet.api.block import Block
from amulet.api.chunk import Chunk
from amulet.api.errors import ChunkDoesNotExist
from amulet.level.formats.anvil_world import AnvilFormat

from helpers.context import SchematicContext
from helpers.fence_adjacency import resolve_fence_adjacency
from helpers.grid import get_worldgen_base_y
from helpers.landscape_utils import generate_full_3d_landscape_sitemap
from helpers.lantern_placement import resolve_lantern_worldgen
from helpers.layer_groups import is_layer_render_visible
from helpers.registry_blocks import (
    get_block_behavior,
    resolve_minecraft_block_id,
    resolve_minecraft_blockstates,
)
from helpers.registry_lookup import get_block_entry, registry_lookup_token
from helpers.structure_tokens import ParsedToken, parse_structure_token
from helpers.types import RawToken
from helpers.worldgen_block_entities import (
    normalize_block_for_worldgen_export,
    resolve_worldgen_export_block_id,
)
from helpers.worldgen_block_updates import schedule_block_update
from helpers.worldgen_multiblock import WorldgenPlacement, parsed_needs_deferred_placement
from helpers.worldgen_region_patch import patch_world_bed_placements
from helpers.worldgen_site import iter_site_landscape_placements

BLOCK_CACHE: dict[ParsedToken, Block] = {}


def resolve_worldgen_token(
    parsed: ParsedToken,
    ctx: SchematicContext,
    layer_array_index: int,
    x: int,
    z: int,
) -> ParsedToken:
    entry = get_block_entry(parsed)

    if entry is None:
        raise ValueError(f"Unknown block token: {registry_lookup_token(parsed)}")

    if get_block_behavior(entry) in {"fence", "wall"}:
        cells = ctx.layers[layer_array_index]["cells"]
        return resolve_fence_adjacency(parsed, cells, x, z)

    if get_block_behavior(entry) == "lantern":
        return resolve_lantern_worldgen(parsed, ctx, layer_array_index, x, z)

    return parsed


def generate_block(parsed: ParsedToken) -> Block:
    cache_key = parsed

    if cache_key in BLOCK_CACHE:
        return BLOCK_CACHE[cache_key]

    entry = get_block_entry(parsed)

    if entry is None:
        raise ValueError(f"Unknown block token: {registry_lookup_token(parsed)}")
    minecraft = entry["minecraft"]

    if "variants" in minecraft:
        variant = parsed.variant or entry.get("defaults", {}).get("variant")

        if variant is None:
            raise ValueError(f"{parsed.token} requires a variant or defaults.variant")

        variant_data = minecraft["variants"][variant]
        block_name = resolve_minecraft_block_id(entry, parsed)
        blockstates_template = variant_data.get("blockstates", {})
    else:
        block_name = resolve_minecraft_block_id(entry, parsed)
        blockstates_template = minecraft.get("blockstates", {})

    resolved_blockstates = resolve_minecraft_blockstates(entry, parsed, blockstates_template)

    if resolved_blockstates:
        state_string = ",".join(f"{key}={value}" for key, value in resolved_blockstates.items())
        generated_block = Block.from_string_blockstate(f"{block_name}[{state_string}]")
    else:
        namespace, base_name = block_name.split(":", 1)
        generated_block = Block(namespace, base_name)

    BLOCK_CACHE[cache_key] = generated_block

    return generated_block


class _ChunkWriter:
    def __init__(self, level: AnvilFormat, dimension: str) -> None:
        self._level = level
        self._dimension = dimension
        self._current_chunk: Chunk | None = None
        self._last_coords: tuple[int, int] | None = None

    def set_block(
        self,
        global_x: int,
        world_y: int,
        global_z: int,
        block: Block,
    ) -> None:
        chunk_x = global_x // 16
        chunk_z = global_z // 16
        chunk_coords = (chunk_x, chunk_z)

        if chunk_coords != self._last_coords:
            if self._current_chunk is not None:
                self._level.commit_chunk(self._current_chunk, self._dimension)

            try:
                self._current_chunk = self._level.load_chunk(chunk_x, chunk_z, self._dimension)
            except ChunkDoesNotExist:
                self._current_chunk = Chunk(chunk_x, chunk_z)

            self._last_coords = chunk_coords

        assert self._current_chunk is not None
        local_x = global_x % 16
        local_z = global_z % 16
        self._current_chunk.set_block(local_x, world_y, local_z, block)
        self._current_chunk.changed = True

    def flush(self) -> None:
        if self._current_chunk is not None:
            self._level.commit_chunk(self._current_chunk, self._dimension)


def _iter_structure_layer_placements(
    ctx: SchematicContext,
) -> Iterator[tuple[int, int, int, RawToken, int, int, int]]:
    base_y = get_worldgen_base_y(ctx)
    offset_x = ctx.grid.get("offset_x", 0)
    offset_z = ctx.grid.get("offset_z", 0)

    for layer_array_index, layer in enumerate(ctx.layers):
        if not is_layer_render_visible(layer, layer_array_index, ctx.grid):
            continue

        actual_y = base_y + layer["index"]

        for z_idx, row in enumerate(layer["cells"]):
            global_z = offset_z + z_idx

            for x_idx, raw_cell in enumerate(row):
                if raw_cell == ".":
                    continue

                global_x = offset_x + x_idx
                yield global_x, actual_y, global_z, raw_cell, layer_array_index, x_idx, z_idx


def _place_parsed_block(
    writer: _ChunkWriter,
    ctx: SchematicContext,
    *,
    global_x: int,
    world_y: int,
    global_z: int,
    parsed: ParsedToken,
    layer_array_index: int | None = None,
    local_x: int | None = None,
    local_z: int | None = None,
) -> None:
    if layer_array_index is not None and local_x is not None and local_z is not None:
        resolved = resolve_worldgen_token(parsed, ctx, layer_array_index, local_x, local_z)
    else:
        resolved = parsed

    entry = get_block_entry(resolved)
    assert entry is not None

    block = normalize_block_for_worldgen_export(generate_block(resolved), entry, resolved)
    writer.set_block(
        global_x,
        world_y,
        global_z,
        block,
    )

    if get_block_behavior(entry) == "bed" and writer._current_chunk is not None:
        block_id = resolve_worldgen_export_block_id(entry, resolved)
        schedule_block_update(
            writer._current_chunk,
            global_x,
            world_y,
            global_z,
            block_id,
        )


def _resolve_structure_placement(
    ctx: SchematicContext,
    *,
    raw_cell: RawToken,
    layer_array_index: int,
    x_idx: int,
    z_idx: int,
) -> tuple[ParsedToken, Block]:
    parsed = parse_structure_token(raw_cell)

    if parsed is None:
        raise ValueError(f"Invalid structure token: {raw_cell}")

    entry = get_block_entry(parsed)
    if entry is None:
        raise ValueError(f"Unknown block token: {registry_lookup_token(parsed)}")

    resolved = resolve_worldgen_token(parsed, ctx, layer_array_index, x_idx, z_idx)
    block = normalize_block_for_worldgen_export(generate_block(resolved), entry, resolved)
    return resolved, block


def _write_site_landscape(
    writer: _ChunkWriter,
    ctx: SchematicContext,
    site_map,
) -> None:
    for global_x, world_y, global_z, raw_token in iter_site_landscape_placements(
        ctx,
        site_map,
        include_ground=True,
        include_lighting=False,
    ):
        parsed = parse_structure_token(raw_token)

        if parsed is None:
            continue

        if get_block_entry(parsed) is None:
            raise ValueError(f"Unknown block token: {registry_lookup_token(parsed)}")

        _place_parsed_block(
            writer,
            ctx,
            global_x=global_x,
            world_y=world_y,
            global_z=global_z,
            parsed=parsed,
        )


def _write_path_lighting(writer: _ChunkWriter, ctx: SchematicContext, site_map) -> None:
    for global_x, world_y, global_z, raw_token in iter_site_landscape_placements(
        ctx,
        site_map,
        include_ground=False,
        include_lighting=True,
    ):
        parsed = parse_structure_token(raw_token)

        if parsed is None:
            continue

        if get_block_entry(parsed) is None:
            raise ValueError(f"Unknown block token: {registry_lookup_token(parsed)}")

        _place_parsed_block(
            writer,
            ctx,
            global_x=global_x,
            world_y=world_y,
            global_z=global_z,
            parsed=parsed,
        )


def _write_structure_layers(
    writer: _ChunkWriter,
    ctx: SchematicContext,
) -> list[WorldgenPlacement]:
    deferred_placements: list[WorldgenPlacement] = []
    bed_placements: list[WorldgenPlacement] = []

    for (
        global_x,
        actual_y,
        global_z,
        raw_cell,
        layer_array_index,
        x_idx,
        z_idx,
    ) in _iter_structure_layer_placements(ctx):
        resolved, block = _resolve_structure_placement(
            ctx,
            raw_cell=raw_cell,
            layer_array_index=layer_array_index,
            x_idx=x_idx,
            z_idx=z_idx,
        )

        if parsed_needs_deferred_placement(resolved):
            placement = WorldgenPlacement(global_x, actual_y, global_z, block, resolved)
            deferred_placements.append(placement)
            if get_block_behavior(get_block_entry(resolved) or {}) == "bed":
                bed_placements.append(placement)
            continue

        _place_parsed_block(
            writer,
            ctx,
            global_x=global_x,
            world_y=actual_y,
            global_z=global_z,
            parsed=resolved,
        )

    if deferred_placements:
        print("🛏️ PLACING MULTI-BLOCK COUPLINGS...")
        for placement in deferred_placements:
            _place_parsed_block(
                writer,
                ctx,
                global_x=placement.global_x,
                world_y=placement.world_y,
                global_z=placement.global_z,
                parsed=placement.parsed,
            )

    return bed_placements


def generate_minecraft_world(ctx: SchematicContext) -> None:
    BLOCK_CACHE.clear()

    if ctx.output_worldgen_dir.exists():
        shutil.rmtree(ctx.output_worldgen_dir)
    shutil.copytree(ctx.worldgen_template_dir, ctx.output_worldgen_dir)

    level = AnvilFormat(ctx.output_worldgen_dir)
    level.open()

    dimension = "minecraft:overworld"
    writer = _ChunkWriter(level, dimension)

    print("🔨 TRANSLATING 3D TOKENS INTO ANVIL CHUNK MATRIX MAPS...")
    site_map = generate_full_3d_landscape_sitemap(ctx)

    print("🌿 WRITING SITE GROUND AND PATHS...")
    _write_site_landscape(writer, ctx, site_map)

    print("🏗️ WRITING STRUCTURE LAYERS...")
    bed_placements = _write_structure_layers(writer, ctx)

    print("🔦 WRITING PATH LIGHTING...")
    _write_path_lighting(writer, ctx, site_map)

    writer.flush()

    print("💾 WRITING BLOCKSTATES TO MCA REGION ARCHIVES...")
    level.save()
    level.close()

    if bed_placements:
        print("🧩 PATCHING BED BLOCK ENTITIES AND POST-LOAD UPDATES...")
        patch_world_bed_placements(ctx.output_worldgen_dir, bed_placements)

    print(f"🎉 SUCCESS! World generated at: ./{ctx.output_worldgen_dir}")
