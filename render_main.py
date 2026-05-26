import random

import helpers.utils as utils
import helpers.constants as constants

from helpers.paths import ASSET_FOLDER, OUTPUT_SCHEMATICS_FOLDER
from helpers.context import SchematicContext
from helpers.types import RenderList

from renderers import structure_facades, top_view, materials, path_view, roof, site_facades, worldgen
from registries.loader import BLOCK_REGISTRY
from registries.loader import compile_texture_set


# --- STATIC GLOBAL MATRIX INITIALIZATION ---
random.seed(42)

# --- MASTER PIPELINE RUNNER WRAPPER ---
def build_stage_complete_schematics(structure: str, stage: int, renders: RenderList = None):
    if renders is None:
        renders = [constants.RENDER_ALL]    

    if isinstance(renders, str):
        renders = [renders]

    renders = set(renders)

    def should_render(name):
        return constants.RENDER_ALL in renders or name in renders

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
    
    ctx.topdown_textures = compile_texture_set(constants.TEXTURE_TOP, ctx.assets_dir, block_px=30)
    ctx.sideview_textures = compile_texture_set(constants.TEXTURE_SIDE, ctx.assets_dir, block_px=30)
    
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
    
    if should_render(constants.RENDER_TOP_VIEW):
        top_view.render_floor_blueprints(ctx)
        
    if should_render(constants.RENDER_ROOF):
        roof.render_roof_blueprints(ctx)

    if should_render(constants.RENDER_STRUCTURE_FACADES):
        structure_facades.render_structure_facades(ctx)

    if should_render(constants.RENDER_PATH):
        path_view.render_path_focused_blueprint(ctx)
    
    if should_render(constants.RENDER_SITE_FACADES):
        site_facades.render_site_facades(ctx)

    if should_render(constants.RENDER_MATERIALS):
        materials.render_materials_inventory_blueprint(ctx)
        
    worldgen.generate_minecraft_world(structure=structure, stage=stage)
    
    print("="*70)
    print(f"🎉 ENGINE COMPLETE! Assets packed to: {target_path.resolve()}")
    print("="*70 + "\n")

if __name__ == "__main__":
    build_stage_complete_schematics(   
        structure="residence",     
        stage=2,
        renders=None)
