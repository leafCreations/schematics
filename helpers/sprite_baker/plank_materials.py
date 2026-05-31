from __future__ import annotations

from pathlib import Path


def list_plank_materials(*, textures_dir: Path) -> list[str]:
    if not textures_dir.exists():
        return ["oak"]

    materials = sorted(
        path.stem.removesuffix("_planks") for path in textures_dir.glob("*_planks.png")
    )
    return materials or ["oak"]


def list_door_materials(*, textures_dir: Path) -> list[str]:
    if not textures_dir.exists():
        return ["oak"]

    materials = sorted(
        path.stem.removesuffix("_door_bottom") for path in textures_dir.glob("*_door_bottom.png")
    )
    return materials or ["oak"]


def expand_material_bake_keys(
    base_keys: list[str],
    *,
    token: str,
    materials: list[str],
) -> list[str]:
    expanded: set[str] = set(base_keys)

    for material in materials:
        for key in base_keys:
            if key == token:
                expanded.add(f"{token}:{material}")
            elif key.startswith(f"{token}#"):
                expanded.add(key.replace(token, f"{token}:{material}", 1))

    return sorted(expanded)
