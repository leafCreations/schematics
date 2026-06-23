import argparse
import random
import sys
from collections.abc import Callable
from pathlib import Path

import helpers.constants as constants
import helpers.pipeline as pipeline
import helpers.utils as utils
from helpers.context import SchematicContext
from helpers.types import RenderList
from renderers.registry import RENDER_REGISTRY

# --- STATIC GLOBAL MATRIX INITIALIZATION ---
random.seed(42)

ProgressCallback = Callable[[str, str], None]


def run_stage_renders(
    structure: str,
    stage: int,
    renders: RenderList | str | None = None,
    *,
    structure_path: Path | None = None,
    worldgen_version: str | None = None,
    progress: ProgressCallback | None = None,
) -> SchematicContext:
    """Load structure from disk and run the selected render handlers."""
    renders = pipeline.normalize_renders(renders)
    pipeline.validate_render_names(renders)

    def should_render(name: str) -> bool:
        return constants.RENDER_ALL in renders or name in renders

    if structure_path is not None:
        from helpers.structure_loader import build_schematic_context, load_structure_yaml

        ctx = build_schematic_context(
            load_structure_yaml(structure_path.resolve()),
            worldgen_version=worldgen_version,
        )
    else:
        ctx = utils.load_structure_config(structure, stage, worldgen_version=worldgen_version)
    ctx.output_schematics_dir.mkdir(parents=True, exist_ok=True)

    if progress is None:
        print("\n" + "=" * 70)
        print("🤖 RUNNING AUTOMATED OMNI-BLUEPRINT COMPILE ENGINE...")
        print("=" * 70)

    for render_name, (label, render_fn) in RENDER_REGISTRY.items():
        if not should_render(render_name):
            continue

        if progress is not None:
            progress(render_name, label)
        else:
            print(f"\n[Render] Generating {label}...")

        render_fn(ctx)

    if progress is None:
        print("=" * 70)
        print("🎉 ENGINE COMPLETE!")
        print("=" * 70 + "\n")

    return ctx


def build_stage_complete_schematics(
    structure: str,
    stage: int,
    renders: RenderList | str | None = None,
    *,
    worldgen_version: str | None = None,
) -> SchematicContext:
    return run_stage_renders(
        structure,
        stage,
        renders,
        worldgen_version=worldgen_version,
    )


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
    parser.add_argument(
        "--worldgen-version",
        default=None,
        metavar="VERSION",
        help="Minecraft version for the worldgen template (e.g. 26.1.2, 26.2)",
    )

    args = parser.parse_args(argv)

    try:
        build_stage_complete_schematics(
            structure=args.structure,
            stage=args.stage,
            renders=args.renders,
            worldgen_version=args.worldgen_version,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
