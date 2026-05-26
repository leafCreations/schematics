import random

import helpers.utils as utils
import helpers.constants as constants

from helpers.context import SchematicContext
from helpers.types import RenderList

from renderers import structure_facades, top_view, materials, path_view, roof, site_facades, worldgen

# --- STATIC GLOBAL MATRIX INITIALIZATION ---
random.seed(42)

# --- MASTER PIPELINE RUNNER WRAPPER ---
def build_stage_complete_schematics(structure: str, stage: int, renders: RenderList | str | None = None):
    if renders is None:
        renders = [constants.RENDER_ALL]    

    if isinstance(renders, str):
        renders = [renders]

    renders = set(renders)

    def should_render(name):
        return constants.RENDER_ALL in renders or name in renders

    ctx: SchematicContext = utils.load_structure_config(structure, stage)    
                
    print("\n" + "="*70)
    print("🤖 RUNNING AUTOMATED OMNI-BLUEPRINT COMPILE ENGINE...")
    print("="*70)            
    
    if should_render(constants.RENDER_TOP_VIEW):
        print("\n[Render] Generating Top-Down Floor Blueprints...")
        top_view.render_floor_blueprints(ctx)
        
    if should_render(constants.RENDER_ROOF):
        print("\n[Render] Generating Roof Blueprints...")
        roof.render_roof_blueprints(ctx)

    if should_render(constants.RENDER_STRUCTURE_FACADES):
        print("\n[Render] Generating Structure Facades...")
        structure_facades.render_structure_facades(ctx)

    if should_render(constants.RENDER_PATH):
        print("\n[Render] Generating Path-Focused Blueprints...")
        path_view.render_path_focused_blueprint(ctx)
    
    if should_render(constants.RENDER_SITE_FACADES):
        print("\n[Render] Generating Site Facades...")
        site_facades.render_site_facades(ctx)

    if should_render(constants.RENDER_MATERIALS):
        print("\n[Render] Generating Materials Inventory Blueprint...")
        materials.render_materials_inventory_blueprint(ctx)
        
    if should_render(constants.RENDER_WORLDGEN):
        print("\n[Render] Generating Minecraft World...")
        worldgen.generate_minecraft_world(ctx)
    
    print("="*70)
    print(f"🎉 ENGINE COMPLETE!")
    print("="*70 + "\n")

if __name__ == "__main__":
    build_stage_complete_schematics(   
        structure="residence",     
        stage=2,
        renders=[constants.RENDER_ALL])
