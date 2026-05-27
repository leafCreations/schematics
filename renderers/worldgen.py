import shutil

from amulet.api.block import Block
from amulet.api.chunk import Chunk
from amulet.api.errors import ChunkDoesNotExist
from amulet.level.formats.anvil_world import AnvilFormat

import helpers.utils as utils
from helpers.context import SchematicContext
from helpers.types import MinecraftBlock
from registries.loader import BLOCK_REGISTRY

BLOCK_CACHE: dict[str, Block] = {}


def generate_block(token: str) -> Block:
    if token in BLOCK_CACHE:
        return BLOCK_CACHE[token]

    block: MinecraftBlock = BLOCK_REGISTRY[token]["minecraft"]

    block_name = block["block"]
    block_state = block.get("blockstate")

    if block_state:
        generated_block = Block.from_string_blockstate(f"{block_name}[{block_state}]")
    else:
        namespace, base_name = block_name.split(":", 1)
        generated_block = Block(namespace, base_name)

    BLOCK_CACHE[token] = generated_block
    return generated_block


def generate_minecraft_world(ctx: SchematicContext):
    if ctx.output_worldgen_dir.exists():
        shutil.rmtree(ctx.output_worldgen_dir)
    shutil.copytree(ctx.worldgen_template_dir, ctx.output_worldgen_dir)

    # Initialize AnvilFormat directly to avoid World() initialization crashes
    level = AnvilFormat(ctx.output_worldgen_dir)

    # 2. CRITICAL: Explicitly open the format
    # This mounts the directory and prepares the internal MCA readers
    level.open()

    # 3. Define the dimension and base Y level for structure placement.
    # Note: The base Y level should be chosen based on the structure's
    # height and desired ground level in the world.
    # For example, base_y = - 60 is used for super flat world.
    dimension = "minecraft:overworld"
    base_y = -60  #

    print("🔨 TRANSLATING 3D TOKENS INTO ANVIL CHUNK MATRIX MAPS...")
    current_chunk = None
    last_coords = None

    for layer_y, lines in ctx.data.items():
        actual_y = base_y + layer_y

        for z_idx, line in enumerate(lines):
            tokens = line.split()
            global_z = ctx.offset_z + z_idx

            for x_idx, token_raw in enumerate(tokens):
                global_x = ctx.offset_x + x_idx
                token = utils.get_base_token(token_raw)

                if token == "." or token not in ctx.block_registry:
                    continue

                chunk_x = global_x // 16
                chunk_z = global_z // 16
                chunk_coords = (chunk_x, chunk_z)

                if chunk_coords != last_coords:
                    if current_chunk is not None:
                        level.commit_chunk(current_chunk, dimension)
                        # print(f"Committed chunk {chunk_x}, {chunk_z}")

                    try:
                        current_chunk = level.load_chunk(chunk_x, chunk_z, dimension)
                    except ChunkDoesNotExist:
                        current_chunk = Chunk(chunk_x, chunk_z)

                    last_coords = chunk_coords

                block_to_place = generate_block(token)

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
