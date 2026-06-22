#!/usr/bin/env python3
"""Bake schematic sprites into assets/minecraft/generated/ for use by compile_texture_set."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER, GENERATED_ASSETS_FOLDER
from helpers.sprite_baker import load_or_bake
from helpers.sprite_baker.cache import cache_path
from helpers.sprite_baker.compose_bed import compose_bed, list_bed_bake_keys
from helpers.sprite_baker.compose_campfire import compose_campfire, list_campfire_bake_keys
from helpers.sprite_baker.compose_chest import compose_chest, list_chest_bake_keys
from helpers.sprite_baker.compose_door import compose_door, list_door_bake_keys
from helpers.sprite_baker.compose_fence import compose_fence, list_fence_bake_keys
from helpers.sprite_baker.compose_lantern import compose_lantern, list_lantern_bake_keys
from helpers.sprite_baker.compose_log import compose_log, list_log_bake_keys
from helpers.sprite_baker.compose_simple import compose_simple, list_simple_bake_keys
from helpers.sprite_baker.compose_slab import compose_slab, list_slab_bake_keys
from helpers.sprite_baker.compose_stairs import compose_stairs, list_stairs_bake_keys
from helpers.sprite_baker.compose_torch import compose_torch, list_torch_bake_keys
from helpers.sprite_baker.compose_trapdoor import compose_trapdoor, list_trapdoor_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError, bake_demo_planks
from helpers.sprite_baker.setup import register_default_composers


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bake schematic block sprites to assets/minecraft/generated/",
    )
    parser.add_argument(
        "--type",
        choices=[
            "simple",
            "slab",
            "stairs",
            "door",
            "bed",
            "chest",
            "fence",
            "torch",
            "lantern",
            "campfire",
            "log",
            "trapdoor",
            "demo",
        ],
        default="simple",
        help=(
            "Bake mode: simple solids, slabs, stairs, doors, trapdoors, beds, chests, "
            "fences, torches, lanterns, campfires, logs, or Phase 0 demo"
        ),
    )
    parser.add_argument(
        "--view",
        default=constants.TEXTURE_TOP,
        choices=[constants.TEXTURE_TOP, constants.TEXTURE_SIDE, "inventory"],
        help="Sprite view folder under assets/minecraft/generated/ (default: top)",
    )
    parser.add_argument(
        "--key",
        help="Registry texture key to bake (for example GRASS or COBBLESTONE#mossy)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Bake all simple solid blocks for the selected view",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=constants.BLOCK_PX,
        help=f"Output sprite size in pixels (default: {constants.BLOCK_PX})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-bake even when a cached sprite already exists",
    )
    parser.add_argument(
        "--textures-dir",
        type=Path,
        default=BLOCK_TEXTURES_FOLDER,
        help="Directory containing vanilla block textures",
    )
    parser.add_argument(
        "--generated-root",
        type=Path,
        default=GENERATED_ASSETS_FOLDER,
        help="Root directory for baked sprite output",
    )
    return parser.parse_args()


def _resolve_keys(args: argparse.Namespace) -> list[str]:
    if args.all:
        if args.type == "simple":
            return list_simple_bake_keys(args.view, textures_dir=args.textures_dir)
        if args.type == "slab":
            return list_slab_bake_keys(args.view, textures_dir=args.textures_dir)
        if args.type == "stairs":
            return list_stairs_bake_keys(args.view, textures_dir=args.textures_dir)
        if args.type == "door":
            return list_door_bake_keys(args.view, textures_dir=args.textures_dir)
        if args.type == "bed":
            return list_bed_bake_keys(args.view)
        if args.type == "chest":
            return list_chest_bake_keys(args.view)
        if args.type == "fence":
            return list_fence_bake_keys(args.view, textures_dir=args.textures_dir)
        if args.type == "torch":
            return list_torch_bake_keys(args.view)
        if args.type == "lantern":
            return list_lantern_bake_keys(args.view)
        if args.type == "campfire":
            return list_campfire_bake_keys(args.view)
        if args.type == "log":
            return list_log_bake_keys(args.view, textures_dir=args.textures_dir)
        if args.type == "trapdoor":
            return list_trapdoor_bake_keys(args.view, textures_dir=args.textures_dir)

        raise SpriteBakeError(
            "--all is only supported with --type simple, slab, stairs, door, trapdoor, "
            "bed, chest, fence, torch, lantern, campfire, or log"
        )

    if args.key:
        return [args.key]

    if args.type == "demo":
        return ["PLANKS"]

    raise SpriteBakeError("Specify --key or use --all")


def _bake_key(args: argparse.Namespace, key: str) -> Path:
    if args.type == "demo":

        def bake_fn():
            return bake_demo_planks(args.size, textures_dir=args.textures_dir)

    elif args.type == "slab":

        def bake_fn():
            return compose_slab(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    elif args.type == "stairs":

        def bake_fn():
            return compose_stairs(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    elif args.type == "door":

        def bake_fn():
            return compose_door(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    elif args.type == "bed":

        def bake_fn():
            return compose_bed(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    elif args.type == "chest":

        def bake_fn():
            return compose_chest(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    elif args.type == "fence":

        def bake_fn():
            return compose_fence(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    elif args.type == "torch":

        def bake_fn():
            return compose_torch(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    elif args.type == "lantern":

        def bake_fn():
            return compose_lantern(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    elif args.type == "log":

        def bake_fn():
            return compose_log(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    elif args.type == "campfire":

        def bake_fn():
            return compose_campfire(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    elif args.type == "trapdoor":

        def bake_fn():
            return compose_trapdoor(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    else:

        def bake_fn():
            return compose_simple(
                key=key,
                view=args.view,
                size=args.size,
                textures_dir=args.textures_dir,
            )

    load_or_bake(
        args.view,
        key,
        bake_fn,
        generated_root=args.generated_root,
        force=args.force,
    )
    return cache_path(args.view, key, generated_root=args.generated_root)


def main() -> int:
    register_default_composers()
    args = _parse_args()

    try:
        keys = _resolve_keys(args)
        output_paths = [_bake_key(args, key) for key in keys]
    except SpriteBakeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for key, output_path in zip(keys, output_paths, strict=True):
        print(f"baked {args.view}/{key} -> {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
