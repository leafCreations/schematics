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


def _build_preview_context(
    structure: str,
    stage: int,
    *,
    structure_path: Path | None = None,
    structure_config: dict | None = None,
    worldgen_version: str | None = None,
) -> SchematicContext:
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    if structure_config is not None:
        return build_schematic_context(structure_config, worldgen_version=worldgen_version)

    if structure_path is not None:
        return build_schematic_context(
            load_structure_yaml(structure_path.resolve()),
            worldgen_version=worldgen_version,
        )

    return utils.load_structure_config(structure, stage, worldgen_version=worldgen_version)


def run_stage_renders(
    structure: str,
    stage: int,
    renders: RenderList | str | None = None,
    *,
    structure_path: Path | None = None,
    worldgen_version: str | None = None,
    output_schematics_dir: Path | None = None,
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
    if output_schematics_dir is not None:
        ctx.output_schematics_dir = output_schematics_dir
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


def run_preview_top_down(
    structure: str,
    stage: int,
    group_name: str,
    *,
    structure_path: Path | None = None,
    structure_config: dict | None = None,
    worldgen_version: str | None = None,
    output_schematics_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> SchematicContext:
    """Render per-Y top-down PNGs for one editor group into the preview session dir."""
    ctx = _build_preview_context(
        structure,
        stage,
        structure_path=structure_path,
        structure_config=structure_config,
        worldgen_version=worldgen_version,
    )

    if output_schematics_dir is not None:
        ctx.output_schematics_dir = output_schematics_dir

    ctx.output_schematics_dir.mkdir(parents=True, exist_ok=True)

    if progress is not None:
        progress(constants.RENDER_TOP_VIEW, f"Top-Down preview ({group_name})")
    else:
        print(f"\n[Preview] Generating top-down layers for {group_name}...")

    from renderers.preview_top_view import render_preview_group_blueprints

    render_preview_group_blueprints(ctx, group_name)
    return ctx


def run_preview_structure_facades(
    structure: str,
    stage: int,
    *,
    structure_path: Path | None = None,
    structure_config: dict | None = None,
    worldgen_version: str | None = None,
    output_schematics_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> SchematicContext:
    """Render per-direction structure facade PNGs into the preview session dir."""
    ctx = _build_preview_context(
        structure,
        stage,
        structure_path=structure_path,
        structure_config=structure_config,
        worldgen_version=worldgen_version,
    )

    if output_schematics_dir is not None:
        ctx.output_schematics_dir = output_schematics_dir

    ctx.output_schematics_dir.mkdir(parents=True, exist_ok=True)

    if progress is not None:
        progress(constants.RENDER_STRUCTURE_FACADES, "Structure Facades preview")
    else:
        print("\n[Preview] Generating structure facade directions...")

    from renderers.preview_structure_facades import render_preview_structure_facades

    render_preview_structure_facades(ctx)
    return ctx


def run_preview_site_facades(
    structure: str,
    stage: int,
    *,
    structure_path: Path | None = None,
    structure_config: dict | None = None,
    worldgen_version: str | None = None,
    output_schematics_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> SchematicContext:
    """Render per-direction site facade PNGs into the preview session dir."""
    ctx = _build_preview_context(
        structure,
        stage,
        structure_path=structure_path,
        structure_config=structure_config,
        worldgen_version=worldgen_version,
    )

    if output_schematics_dir is not None:
        ctx.output_schematics_dir = output_schematics_dir

    ctx.output_schematics_dir.mkdir(parents=True, exist_ok=True)

    if progress is not None:
        progress(constants.RENDER_SITE_FACADES, "Site Facades preview")
    else:
        print("\n[Preview] Generating site facade directions...")

    from renderers.preview_site_facades import render_preview_site_facades

    render_preview_site_facades(ctx)
    return ctx


def run_preview_site_top_down(
    structure: str,
    stage: int,
    *,
    structure_path: Path | None = None,
    structure_config: dict | None = None,
    worldgen_version: str | None = None,
    output_schematics_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> SchematicContext:
    """Render per-Y site top-down PNGs into the preview session dir."""
    ctx = _build_preview_context(
        structure,
        stage,
        structure_path=structure_path,
        structure_config=structure_config,
        worldgen_version=worldgen_version,
    )

    if output_schematics_dir is not None:
        ctx.output_schematics_dir = output_schematics_dir

    ctx.output_schematics_dir.mkdir(parents=True, exist_ok=True)

    if progress is not None:
        progress(constants.RENDER_PATH, "Site Top Down preview")
    else:
        print("\n[Preview] Generating site top-down layers...")

    from renderers.preview_site_topdown import render_preview_site_topdown

    render_preview_site_topdown(ctx)
    return ctx


def run_preview_materials(
    structure: str,
    stage: int,
    *,
    structure_path: Path | None = None,
    structure_config: dict | None = None,
    worldgen_version: str | None = None,
    output_schematics_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> SchematicContext:
    """Render materials list PNG into the preview session dir."""
    ctx = _build_preview_context(
        structure,
        stage,
        structure_path=structure_path,
        structure_config=structure_config,
        worldgen_version=worldgen_version,
    )

    if output_schematics_dir is not None:
        ctx.output_schematics_dir = output_schematics_dir

    ctx.output_schematics_dir.mkdir(parents=True, exist_ok=True)

    if progress is not None:
        progress(constants.RENDER_MATERIALS, "Materials List preview")
    else:
        print("\n[Preview] Generating materials list...")

    from renderers.preview_materials import render_preview_materials

    render_preview_materials(ctx)
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
