from __future__ import annotations

from pathlib import Path


def list_plank_materials(*, textures_dir: Path) -> list[str]:
    if not textures_dir.exists():
        return ["oak"]

    materials = sorted(
        path.stem.removesuffix("_planks") for path in textures_dir.glob("*_planks.png")
    )
    return materials or ["oak"]


def list_catalog_template_materials(block_template: str) -> list[str]:
    from helpers.block_picker import enumerate_token_materials

    return list(enumerate_token_materials(block_template))


def list_stairs_materials(*, textures_dir: Path | None = None) -> list[str]:
    materials = list_catalog_template_materials("minecraft:{material}_stairs")

    if materials:
        return materials

    if textures_dir is not None:
        return list_plank_materials(textures_dir=textures_dir)

    return ["oak"]


def list_slab_materials(*, textures_dir: Path | None = None) -> list[str]:
    materials = list_catalog_template_materials("minecraft:{material}_slab")

    if materials:
        return materials

    if textures_dir is not None:
        return list_plank_materials(textures_dir=textures_dir)

    return ["oak"]


def list_door_materials(*, textures_dir: Path | None = None) -> list[str]:
    materials = list_catalog_template_materials("minecraft:{material}_door")

    if materials:
        return materials

    if textures_dir is not None and textures_dir.exists():
        discovered = sorted(
            path.stem.removesuffix("_door_bottom")
            for path in textures_dir.glob("*_door_bottom.png")
        )

        if discovered:
            return discovered

    return ["oak"]


# Waxed copper blocks reuse unwaxed oxidation-stage textures in vanilla.
WAXED_COPPER_TEXTURE_ALIASES: dict[str, str] = {
    "waxed_copper": "copper",
    "waxed_exposed_copper": "exposed_copper",
    "waxed_weathered_copper": "weathered_copper",
    "waxed_oxidized_copper": "oxidized_copper",
}


def copper_family_texture_material(material: str) -> str:
    return WAXED_COPPER_TEXTURE_ALIASES.get(material, material)


def list_trapdoor_materials(*, textures_dir: Path | None = None) -> list[str]:
    materials = list_catalog_template_materials("minecraft:{material}_trapdoor")

    if materials:
        return materials

    if textures_dir is not None and textures_dir.exists():
        discovered = sorted(
            path.stem.removesuffix("_trapdoor") for path in textures_dir.glob("*_trapdoor.png")
        )

        if discovered:
            return discovered

    return ["oak"]


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
