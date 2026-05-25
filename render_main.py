from helpers.paths import ASSET_FOLDER, OUTPUT_SCHEMATICS_FOLDER

import random
import helpers.utils as utils
from helpers.context import SchematicContext

from renderers import top_view, side_view, materials, path_view

from registries.loader import BLOCK_REGISTRY
from registries.loader import compile_texture_set

# --- STATIC GLOBAL MATRIX INITIALIZATION ---
random.seed(42)

# --- MASTER PIPELINE RUNNER WRAPPER ---
def build_stage_complete_schematics(structure="structure", stage=1, renders=["top_view"]):
    if renders is None:
        renders = ["all"]

    renders = set(renders)

    def should_render(name):
        return "all" in renders or name in renders

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
    
    if should_render("top_view"):
        top_view.render_floor_blueprints(ctx)

    if should_render("side_view"):
        side_view.render_structure_elevations(ctx)

    if should_render("path"):
        path_view.render_path_focused_blueprint(ctx)
        path_view.render_site_elevations(ctx)

    if should_render("materials"):
        materials.render_materials_inventory_blueprint(ctx)
    
    print("="*70)
    print(f"🎉 ENGINE COMPLETE! Assets packed to: {target_path.resolve()}")
    print("="*70 + "\n")

if __name__ == "__main__":
    build_stage_complete_schematics(   
        structure="residence",     
        stage=2)
