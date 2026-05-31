import shutil

from amulet.api.block import Block
from amulet.api.chunk import Chunk
from amulet.api.errors import ChunkDoesNotExist
from amulet.level.formats.anvil_world import AnvilFormat

from helpers.context import SchematicContext
from helpers.fence_adjacency import resolve_fence_adjacency
from helpers.grid import get_worldgen_base_y
from helpers.registry_blocks import (
    get_block_behavior,
    resolve_minecraft_block_id,
    resolve_minecraft_blockstates,
)
from helpers.structure_tokens import ParsedToken, parse_structure_token
from registries.loader import BLOCK_REGISTRY

BLOCK_CACHE: dict[ParsedToken, Block] = {}


def resolve_worldgen_token(
    parsed: ParsedToken,
    cells: list[list[str]],
    x: int,
    z: int,
) -> ParsedToken:
    entry = BLOCK_REGISTRY[parsed.token]

    if get_block_behavior(entry) == "fence":
        return resolve_fence_adjacency(parsed, cells, x, z)

    return parsed


def generate_block(parsed: ParsedToken) -> Block:
    cache_key = parsed

    if cache_key in BLOCK_CACHE:
        return BLOCK_CACHE[cache_key]

    entry = BLOCK_REGISTRY[parsed.token]
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


def generate_minecraft_world(ctx: SchematicContext) -> None:
    BLOCK_CACHE.clear()

    if ctx.output_worldgen_dir.exists():
        shutil.rmtree(ctx.output_worldgen_dir)
    shutil.copytree(ctx.worldgen_template_dir, ctx.output_worldgen_dir)

    level = AnvilFormat(ctx.output_worldgen_dir)
    level.open()

    dimension = "minecraft:overworld"
    base_y = get_worldgen_base_y(ctx)

    print("🔨 TRANSLATING 3D TOKENS INTO ANVIL CHUNK MATRIX MAPS...")
    current_chunk = None
    last_coords = None

    for layer in ctx.layers:
        actual_y = base_y + layer["index"]

        for z_idx, row in enumerate(layer["cells"]):
            global_z = ctx.grid["offset_z"] + z_idx

            for x_idx, raw_cell in enumerate(row):
                parsed = parse_structure_token(raw_cell)

                if parsed is None:
                    continue

                if parsed.token not in ctx.block_registry:
                    raise KeyError(f"Unknown block token: {parsed.token}")

                global_x = ctx.grid["offset_x"] + x_idx

                chunk_x = global_x // 16
                chunk_z = global_z // 16
                chunk_coords = (chunk_x, chunk_z)

                if chunk_coords != last_coords:
                    if current_chunk is not None:
                        level.commit_chunk(current_chunk, dimension)

                    try:
                        current_chunk = level.load_chunk(chunk_x, chunk_z, dimension)
                    except ChunkDoesNotExist:
                        current_chunk = Chunk(chunk_x, chunk_z)

                    last_coords = chunk_coords

                resolved = resolve_worldgen_token(parsed, layer["cells"], x_idx, z_idx)
                block_to_place = generate_block(resolved)

                current_chunk.set_block(
                    global_x % 16,
                    actual_y,
                    global_z % 16,
                    block_to_place,
                )
                current_chunk.changed = True

    if current_chunk is not None:
        level.commit_chunk(current_chunk, dimension)

    print("💾 WRITING BLOCKSTATES TO MCA REGION ARCHIVES...")
    level.save()
    level.close()
    print(f"🎉 SUCCESS! World generated at: ./{ctx.output_worldgen_dir}")
