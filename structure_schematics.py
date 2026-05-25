from __init__ import ASSET_FOLDER, OUTPUT_SCHEMATICS_FOLDER

import random
import helpers.utils as utils
from helpers.context import SchematicContext

from renderers import top_view, side_view, materials, path_view

from registries.loader import BLOCK_REGISTRY
from registries.loader import compile_texture_set

# --- STATIC GLOBAL MATRIX INITIALIZATION ---
random.seed(42)

# --- MASTER PIPELINE RUNNER WRAPPER ---
def build_stage_complete_schematics(structure="structure", stage=1):    

    config = utils.load_structure_config(structure, stage)
    
    ctx = SchematicContext(
        data=config["data"],
        site_size=config["size"],
        struct_w=config["struct_w"],
        struct_h=config["struct_h"],
        offset_x=config["offset_x"],
        offset_z=config["offset_z"],
        name=config["name"],
        output_folder=config["output_folder"],
        floor_map=config["floor_map"],
        block_registry=BLOCK_REGISTRY,
        assets_dir=ASSET_FOLDER / "textures/block",
        output_dir=OUTPUT_SCHEMATICS_FOLDER / config["output_folder"]
    )
    
    ctx.topdown_textures = compile_texture_set("top", ctx.assets_dir, block_px=30)
    ctx.sideview_textures = compile_texture_set("side", ctx.assets_dir, block_px=30)
    
    # 1. Define the specific sub-folder path   
    target_path = ctx.output_dir
    if not target_path.exists():
        target_path.mkdir(parents=True)
        print(f"[System Info] Created blueprint directory: {target_path}")
        
    # 2. Define the assets directory path
    assets_directory = ctx.assets_dir
    if not assets_directory.exists():
        raise FileNotFoundError(f"Assets directory not found: {assets_directory}")                
                
    print("\n" + "="*70)
    print("🤖 RUNNING AUTOMATED OMNI-BLUEPRINT COMPILE ENGINE...")
    print("="*70)            
    
    # 3. Render the top-down floor blueprints
    top_view.render_floor_blueprints(ctx)    
    
    # 4. Update the other Nodes to save into 'target_path' as well    
    side_view.render_structure_elevations(ctx)
    
    # 5. Render the path-focused blueprint
    path_view.render_path_focused_blueprint(ctx)        
    path_view.render_site_elevations(ctx)
    
    # 6. Render the materials inventory blueprint
    materials.render_materials_inventory_blueprint(ctx)
    
    print("="*70)
    print(f"🎉 ENGINE COMPLETE! Assets packed to: {target_path.resolve()}")
    print("="*70 + "\n")

if __name__ == "__main__":
    build_stage_complete_schematics(   
        structure="residence",     
        stage=2)
