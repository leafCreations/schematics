import shutil

from amulet.api.block import Block
from amulet.api.chunk import Chunk
from amulet.api.errors import ChunkDoesNotExist
from amulet.level.formats.anvil_world import AnvilFormat

from helpers.context import SchematicContext
from helpers.structure_tokens import ParsedToken, parse_structure_token
from registries.loader import BLOCK_REGISTRY

BLOCK_CACHE: dict[ParsedToken, Block] = {}

DIRECTION_OFFSETS = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}

FENCE_CONNECTABLE_BEHAVIORS = {
    "solid",
    "facing_block",
    "fence",
    "log",
    "slab",
    "stairs",
    "door",
    "bed",
    "chest",
}


def get_cell_at(cells: list[list[str]], x: int, z: int) -> str | None:
    if z < 0 or z >= len(cells):
        return None

    row = cells[z]

    if x < 0 or x >= len(row):
        return None

    return row[x]


def should_fence_connect(raw_neighbor: str | None) -> bool:
    if raw_neighbor is None:
        return False

    parsed_neighbor = parse_structure_token(raw_neighbor)

    if parsed_neighbor is None:
        return False

    entry = BLOCK_REGISTRY.get(parsed_neighbor.token)

    if entry is None:
        return False

    return entry["behavior"] in FENCE_CONNECTABLE_BEHAVIORS


def resolve_fence_adjacency(
    parsed: ParsedToken,
    cells: list[list[str]],
    x: int,
    z: int,
) -> ParsedToken:
    states = tuple(
        (direction, should_fence_connect(get_cell_at(cells, x + dx, z + dz)))
        for direction, (dx, dz) in DIRECTION_OFFSETS.items()
    )

    return ParsedToken(
        token=parsed.token,
        material=parsed.material,
        direction=parsed.direction,
        variant=parsed.variant,
        states=states,
    )


def resolve_worldgen_token(
    parsed: ParsedToken,
    cells: list[list[str]],
    x: int,
    z: int,
) -> ParsedToken:
    entry = BLOCK_REGISTRY[parsed.token]

    if entry["behavior"] == "fence":
        return resolve_fence_adjacency(parsed, cells, x, z)

    return parsed


def generate_block(parsed: ParsedToken) -> Block:
    cache_key = parsed

    if cache_key in BLOCK_CACHE:
        return BLOCK_CACHE[cache_key]

    entry = BLOCK_REGISTRY[parsed.token]

    defaults = entry.get("defaults", {})

    material = parsed.material or entry.get("material_default")
    direction = parsed.direction or defaults.get("direction")
    variant = parsed.variant or defaults.get("variant")

    minecraft = entry["minecraft"]

    #
    # Resolve variant
    #
    if "variants" in minecraft:
        if variant is None:
            raise ValueError(f"{parsed.token} requires a variant or defaults.variant")

        variant_data = minecraft["variants"][variant]
        block_name = variant_data["block"]
        blockstates_template = variant_data.get("blockstates", {})
    else:
        block_name = minecraft["block"]
        blockstates_template = minecraft.get("blockstates", {})

    #
    # Material substitution
    #
    if material:
        block_name = block_name.format(material=material)

    #
    # Resolve blockstates
    #
    resolved_blockstates = {}

    format_values = {
        **defaults,
        **dict(parsed.states),
        "material": material,
        "direction": direction,
        "variant": variant,
        "half": parsed.variant or defaults.get("half"),
        "part": parsed.variant or defaults.get("part"),
        "type": parsed.variant or defaults.get("type"),
        "shape": parsed.variant or defaults.get("shape"),
    }

    for state_name, state_value in blockstates_template.items():
        if isinstance(state_value, str):
            resolved_value = state_value.format(**format_values)
        else:
            resolved_value = state_value

        resolved_blockstates[state_name] = str(resolved_value).lower()

    #
    # Create block
    #
    if resolved_blockstates:
        state_string = ",".join(f"{key}={value}" for key, value in resolved_blockstates.items())

        generated_block = Block.from_string_blockstate(f"{block_name}[{state_string}]")
    else:
        namespace, base_name = block_name.split(":", 1)
        generated_block = Block(namespace, base_name)

    BLOCK_CACHE[cache_key] = generated_block

    return generated_block


def generate_minecraft_world(ctx: SchematicContext) -> None:
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
                        # print(f"Committed chunk {chunk_x}, {chunk_z}")

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
