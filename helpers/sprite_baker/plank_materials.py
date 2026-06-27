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
    "waxed_cut_copper": "cut_copper",
    "waxed_exposed_cut_copper": "exposed_cut_copper",
    "waxed_weathered_cut_copper": "weathered_cut_copper",
    "waxed_oxidized_cut_copper": "oxidized_cut_copper",
}


def copper_family_texture_material(material: str) -> str:
    return WAXED_COPPER_TEXTURE_ALIASES.get(material, material)


# Catalog ``minecraft:{material}_stairs`` stems that do not match ``{material}.png`` on disk.
STAIRS_TEXTURE_MATERIAL_ALIASES: dict[str, str] = {
    "smooth_quartz": "quartz_block_bottom",
    "smooth_sandstone": "sandstone_top",
    "smooth_red_sandstone": "red_sandstone_top",
}


def stairs_texture_material(material: str) -> str:
    copper_alias = copper_family_texture_material(material)
    if copper_alias != material:
        return copper_alias
    explicit = STAIRS_TEXTURE_MATERIAL_ALIASES.get(material)
    if explicit is not None:
        return explicit
    if material.endswith("bricks") or material.endswith("_tiles"):
        return material
    if material == "brick" or material.endswith("_brick"):
        return f"{material}s"
    if material.endswith("_tile"):
        return f"{material}s"
    return material


def stairs_texture_filename_candidates(material: str) -> tuple[str, ...]:
    """Ordered PNG filenames to try when baking ``STAIRS:{material}`` top/side sprites."""
    texture_material = stairs_texture_material(material)
    seen: set[str] = set()
    ordered: list[str] = []

    def add(*names: str) -> None:
        for name in names:
            if name not in seen:
                seen.add(name)
                ordered.append(name)

    add(
        f"{texture_material}_planks.png",
        f"{texture_material}.png",
        f"{texture_material}_stairs.png",
    )
    if texture_material != material:
        add(
            f"{material}_planks.png",
            f"{material}.png",
            f"{material}_stairs.png",
        )
    add(
        f"{material}_block_top.png",
        f"{material}_block.png",
    )
    return tuple(ordered)


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
