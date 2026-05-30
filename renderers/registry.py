from collections.abc import Callable

import helpers.constants as constants
from helpers.context import SchematicContext
from renderers import (
    materials,
    path_view,
    roof,
    site_facades,
    structure_facades,
    top_view,
    worldgen,
)

RenderFn = Callable[[SchematicContext], None]

RENDER_REGISTRY: dict[str, tuple[str, RenderFn]] = {
    constants.RENDER_TOP_VIEW: (
        "Top-Down Floor Blueprints",
        top_view.render_floor_blueprints,
    ),
    constants.RENDER_ROOF: (
        "Roof Blueprints",
        roof.render_roof_blueprints,
    ),
    constants.RENDER_STRUCTURE_FACADES: (
        "Structure Facades",
        structure_facades.render_structure_facades,
    ),
    constants.RENDER_PATH: (
        "Path-Focused Blueprints",
        path_view.render_path_focused_blueprint,
    ),
    constants.RENDER_SITE_FACADES: (
        "Site Facades",
        site_facades.render_site_facades,
    ),
    constants.RENDER_MATERIALS: (
        "Materials Inventory Blueprint",
        materials.render_materials_inventory_blueprint,
    ),
    constants.RENDER_WORLDGEN: (
        "Minecraft World",
        worldgen.generate_minecraft_world,
    ),
}
