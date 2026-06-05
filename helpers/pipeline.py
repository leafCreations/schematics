import helpers.constants as constants

VALID_RENDERERS = {
    constants.RENDER_TOP_VIEW,
    constants.RENDER_ROOF,
    constants.RENDER_STRUCTURE_FACADES,
    constants.RENDER_PATH,
    constants.RENDER_MATERIALS,
    constants.RENDER_WORLDGEN,
}


def normalize_renders(renders):
    if renders is None:
        return {constants.RENDER_ALL}

    if isinstance(renders, str):
        renders = [renders]

    return set(renders)


def validate_render_names(renders: set[str]) -> None:
    unknown = renders - {constants.RENDER_ALL} - VALID_RENDERERS

    if unknown:
        valid = ", ".join(sorted(VALID_RENDERERS))
        unknown_list = ", ".join(sorted(unknown))
        raise ValueError(f"Unknown render type(s): {unknown_list}. Valid: {valid}, all")
