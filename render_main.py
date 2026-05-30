import random

import helpers.constants as constants
import helpers.utils as utils
from helpers.context import SchematicContext
from helpers.types import RenderList
from renderers.registry import RENDER_REGISTRY

# --- STATIC GLOBAL MATRIX INITIALIZATION ---
random.seed(42)


# --- MASTER PIPELINE RUNNER WRAPPER ---
def build_stage_complete_schematics(
    structure: str, stage: int, renders: RenderList | str | None = None
):
    if renders is None:
        renders = [constants.RENDER_ALL]

    if isinstance(renders, str):
        renders = [renders]

    renders = set(renders)

    def should_render(name):
        return constants.RENDER_ALL in renders or name in renders

    ctx: SchematicContext = utils.load_structure_config(structure, stage)

    ctx.output_schematics_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("🤖 RUNNING AUTOMATED OMNI-BLUEPRINT COMPILE ENGINE...")
    print("=" * 70)

    for render_name, (label, render_fn) in RENDER_REGISTRY.items():
        if should_render(render_name):
            print(f"\n[Render] Generating {label}...")
            render_fn(ctx)

    print("=" * 70)
    print("🎉 ENGINE COMPLETE!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    build_stage_complete_schematics(
        structure="residence",
        stage=2,
        renders=[constants.RENDER_ALL],
    )
