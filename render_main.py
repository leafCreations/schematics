import argparse
import random
import sys

import helpers.constants as constants
import helpers.pipeline as pipeline
import helpers.utils as utils
from helpers.types import RenderList
from renderers.registry import RENDER_REGISTRY

# --- STATIC GLOBAL MATRIX INITIALIZATION ---
random.seed(42)


def build_stage_complete_schematics(
    structure: str, stage: int, renders: RenderList | str | None = None
):
    renders = pipeline.normalize_renders(renders)
    pipeline.validate_render_names(renders)

    def should_render(name):
        return constants.RENDER_ALL in renders or name in renders

    ctx = utils.load_structure_config(structure, stage)

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Minecraft schematic blueprints")
    parser.add_argument("--structure", default="residence", help="Structure package name")
    parser.add_argument("--stage", type=int, default=1, help="Structure stage number")
    parser.add_argument(
        "--renders",
        nargs="+",
        default=[constants.RENDER_ALL],
        help="Render types to generate, or 'all'",
    )

    args = parser.parse_args(argv)

    try:
        build_stage_complete_schematics(
            structure=args.structure,
            stage=args.stage,
            renders=args.renders,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
