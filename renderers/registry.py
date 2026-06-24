import sys
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
)

RenderFn = Callable[[SchematicContext], None]


def _render_worldgen(ctx: SchematicContext) -> None:
    try:
        from renderers import worldgen
    except ModuleNotFoundError as exc:
        missing = exc.name or ""
        if missing == "amulet" or missing.startswith("amulet"):
            py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            raise RuntimeError(
                "Worldgen requires amulet-core, which is not installed in this environment.\n\n"
                "Install worldgen dependencies (Python 3.11 required):\n"
                '  pip install -e ".[dev]"\n'
                "  ./scripts/install_worldgen.sh --reuse\n\n"
                "Or build from source (slow):\n"
                "  ./scripts/install_worldgen.sh\n\n"
                f"This interpreter is Python {py_version}."
            ) from exc
        raise

    worldgen.generate_minecraft_world(ctx)


# In-app preview dropdown (top-down per group; facades per direction; site top-down per Y).
PREVIEW_RENDER_REGISTRY: dict[str, str] = {
    constants.RENDER_TOP_VIEW: "Top Down",
    constants.RENDER_STRUCTURE_FACADES: "Structure Facades",
    constants.RENDER_SITE_FACADES: "Site Facades",
    constants.RENDER_PATH: "Site Top Down",
    constants.RENDER_MATERIALS: "Materials List",
}

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
        _render_worldgen,
    ),
}
