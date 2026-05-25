import os
import sys
import shutil

from __init__ import OUTPUT_WORLDS_FOLDER, TEMPLATE_FOLDER
import helpers.utils as utils

# 1. Force Python to register active virtual environment paths safely
import site
venv_site = [p for p in site.getsitepackages() if "site-packages" in p]
if venv_site:
    sys.path.insert(0, venv_site[0])

from amulet.api.block import Block
from amulet.level.formats.anvil_world import AnvilFormat

# --- ENGINE CONFIGURATIONS ---
#STRUCT_W = 9
#STRUCT_H = 10
#STRUCT_OFFSET_X = 10
#STRUCT_OFFSET_Z = 4

STAIR = "half=bottom,waterlogged=false"

BLOCK_PALETTE = {
    "G": Block("minecraft", "grass_block"),
    "C": Block("minecraft", "cobblestone"),
    "M": Block("minecraft", "mossy_cobblestone"),
    "L": Block.from_string_blockstate("minecraft:oak_log[axis=y]"),
    "LS": Block.from_string_blockstate("minecraft:oak_log[axis=x]"),
    "P": Block("minecraft", "oak_planks"),    
    "F": Block.from_string_blockstate("minecraft:furnace[facing=west]"),
    "T": Block("minecraft", "crafting_table"),
    "cf": Block.from_string_blockstate(
        "minecraft:campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]"
    ),

    # FENCE
    ## no connections
    "o": Block.from_string_blockstate(
        "minecraft:oak_fence[north=false,east=false,south=false,west=false,waterlogged=false]"
    ),

    ## single connections
    "on": Block.from_string_blockstate(
        "minecraft:oak_fence[north=true,east=false,south=false,west=false,waterlogged=false]"
    ),
    "oe": Block.from_string_blockstate(
        "minecraft:oak_fence[north=false,east=true,south=false,west=false,waterlogged=false]"
    ),
    "os": Block.from_string_blockstate(
        "minecraft:oak_fence[north=false,east=false,south=true,west=false,waterlogged=false]"
    ),
    "ow": Block.from_string_blockstate(
        "minecraft:oak_fence[north=false,east=false,south=false,west=true,waterlogged=false]"
    ),

    ## two-way connections
    "ons": Block.from_string_blockstate(
        "minecraft:oak_fence[north=true,east=false,south=true,west=false,waterlogged=false]"
    ),
    "oew": Block.from_string_blockstate(
        "minecraft:oak_fence[north=false,east=true,south=false,west=true,waterlogged=false]"
    ),

    ## corners
    "one": Block.from_string_blockstate(
        "minecraft:oak_fence[north=true,east=true,south=false,west=false,waterlogged=false]"
    ),
    "onw": Block.from_string_blockstate(
        "minecraft:oak_fence[north=true,east=false,south=false,west=true,waterlogged=false]"
    ),
    "ose": Block.from_string_blockstate(
        "minecraft:oak_fence[north=false,east=true,south=true,west=false,waterlogged=false]"
    ),
    "osw": Block.from_string_blockstate(
        "minecraft:oak_fence[north=false,east=false,south=true,west=true,waterlogged=false]"
    ),

    # STAIRS
    ## straight sides
    "sn": Block.from_string_blockstate(f"minecraft:oak_stairs[facing=north,shape=straight,{STAIR}]"),
    "ss": Block.from_string_blockstate(f"minecraft:oak_stairs[facing=south,shape=straight,{STAIR}]"),
    "se": Block.from_string_blockstate(f"minecraft:oak_stairs[facing=east,shape=straight,{STAIR}]"),
    "sw": Block.from_string_blockstate(f"minecraft:oak_stairs[facing=west,shape=straight,{STAIR}]"),

    ## roof outer corners
    "sn_ol": Block.from_string_blockstate(f"minecraft:oak_stairs[facing=north,shape=outer_left,{STAIR}]"),
    "sn_or": Block.from_string_blockstate(f"minecraft:oak_stairs[facing=north,shape=outer_right,{STAIR}]"),
    "ss_ol": Block.from_string_blockstate(f"minecraft:oak_stairs[facing=south,shape=outer_left,{STAIR}]"),
    "ss_or": Block.from_string_blockstate(f"minecraft:oak_stairs[facing=south,shape=outer_right,{STAIR}]"),
    "l": Block.from_string_blockstate(
        "minecraft:oak_slab[type=bottom,waterlogged=false]"
    ),

    # TORCHES
    "it": Block.from_string_blockstate("minecraft:torch"),
    "in": Block.from_string_blockstate("minecraft:wall_torch[facing=north]"),
    "is": Block.from_string_blockstate("minecraft:wall_torch[facing=south]"),
    "ie": Block.from_string_blockstate("minecraft:wall_torch[facing=east]"),
    "iw": Block.from_string_blockstate("minecraft:wall_torch[facing=west]"),    

    # DOOR
    "dt": Block.from_string_blockstate(
        "minecraft:oak_door[facing=east,half=upper,hinge=left,open=false,powered=false]"
    ),
    "db": Block.from_string_blockstate(
    "minecraft:oak_door[facing=east,half=lower,hinge=left,open=false,powered=false]"
    ),

    # CHEST
    "xn_l": Block.from_string_blockstate(
        "minecraft:chest[facing=north,type=left,waterlogged=false]"
    ),
    "xn_r": Block.from_string_blockstate(
        "minecraft:chest[facing=north,type=right,waterlogged=false]"
    ),

    "xs_l": Block.from_string_blockstate(
        "minecraft:chest[facing=south,type=left,waterlogged=false]"
    ),
    "xs_r": Block.from_string_blockstate(
        "minecraft:chest[facing=south,type=right,waterlogged=false]"
    ),

    "xe_l": Block.from_string_blockstate(
        "minecraft:chest[facing=east,type=left,waterlogged=false]"
    ),
    "xe_r": Block.from_string_blockstate(
        "minecraft:chest[facing=east,type=right,waterlogged=false]"
    ),

    "xw_l": Block.from_string_blockstate(
        "minecraft:chest[facing=west,type=left,waterlogged=false]"
    ),
    "xw_r": Block.from_string_blockstate(
        "minecraft:chest[facing=west,type=right,waterlogged=false]"
    ),

    # BED    
    "bn_f": Block.from_string_blockstate(
        "minecraft:red_bed[facing=north,part=foot,occupied=false]"
    ),
    "bn_h": Block.from_string_blockstate(
        "minecraft:red_bed[facing=north,part=head,occupied=false]"
    ),    
    "bs_f": Block.from_string_blockstate(
        "minecraft:red_bed[facing=south,part=foot,occupied=false]"
    ),
    "bs_h": Block.from_string_blockstate(
        "minecraft:red_bed[facing=south,part=head,occupied=false]"
    ),
    "be_f": Block.from_string_blockstate(
        "minecraft:red_bed[facing=east,part=foot,occupied=false]"
    ),
    "be_h": Block.from_string_blockstate(
        "minecraft:red_bed[facing=east,part=head,occupied=false]"
    ),
    "bw_f": Block.from_string_blockstate(
        "minecraft:red_bed[facing=west,part=foot,occupied=false]"
    ),
    "bw_h": Block.from_string_blockstate(
        "minecraft:red_bed[facing=west,part=head,occupied=false]"
    ),
}

def generate_minecraft_world(structure=None, stage=1):
        
    global STRUCTURE_DATA_3D
    global SITE_SIZE
    global STRUCT_W
    global STRUCT_H
    global STRUCT_OFFSET_X
    global STRUCT_OFFSET_Z

    config = utils.load_structure_config(structure, stage);
    
    STRUCTURE_DATA_3D = config["data"]
    STRUCT_W = config["struct_w"]
    STRUCT_H = config["struct_h"]
    STRUCT_OFFSET_X = config["offset_x"]
    STRUCT_OFFSET_Z = config["offset_z"]
    
    target_world_folder = OUTPUT_WORLDS_FOLDER / config["output_folder"]
    
    if os.path.exists(target_world_folder):
        shutil.rmtree(target_world_folder)
    shutil.copytree(TEMPLATE_FOLDER, target_world_folder)
    
    # Initialize AnvilFormat directly to avoid World() initialization crashes
    level = AnvilFormat(target_world_folder)

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

    for layer_y, lines in STRUCTURE_DATA_3D.items():
        actual_y = base_y + layer_y
        for z_idx, line in enumerate(lines):
            tokens = line.split()
            global_z = STRUCT_OFFSET_Z + z_idx
            for x_idx, token_raw in enumerate(tokens):
                global_x = STRUCT_OFFSET_X + x_idx
                token = token_raw.split("@")[0]
                
                if token == "." or token not in BLOCK_PALETTE:
                    continue
                
                # Fetch chunk via format directly
                chunk_x = global_x // 16
                chunk_z = global_z // 16
                chunk_coords = (chunk_x, chunk_z)

                changed_chunks = {}
                
                if chunk_coords != last_coords:
                    # 'load_chunk' is available in your API version
                    current_chunk = level.load_chunk(chunk_x, chunk_z, dimension)
                    last_coords = chunk_coords
                                
                block_to_place = BLOCK_PALETTE[token]                
                current_chunk.set_block(global_x % 16, actual_y, global_z % 16, block_to_place)
                current_chunk.changed = True
                changed_chunks[chunk_coords] = current_chunk

                for coords, chunk in changed_chunks.items():
                    level.commit_chunk(current_chunk, dimension)                
                
                    
    print("💾 WRITING BLOCKSTATES TO MCA REGION ARCHIVES...")
    level.save()
    level.close()
    print(f"🎉 SUCCESS! World generated at: ./{target_world_folder}")

if __name__ == "__main__":
    my_template = os.path.join(os.getcwd(), "template")
    my_output = os.path.join(os.getcwd(), "Residence_World")
    generate_minecraft_world(
        structure="residence",
        stage=2
    )
