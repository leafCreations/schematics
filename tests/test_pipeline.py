import pytest

import helpers.constants as constants
import helpers.pipeline as pipeline


def test_validate_render_names_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown render type"):
        pipeline.validate_render_names({"not_a_renderer"})


def test_validate_render_names_accepts_all_and_known():
    pipeline.validate_render_names({constants.RENDER_ALL, constants.RENDER_TOP_VIEW})


def test_renders_include_worldgen():
    assert pipeline.renders_include_worldgen([constants.RENDER_ALL])
    assert pipeline.renders_include_worldgen([constants.RENDER_WORLDGEN])
    assert not pipeline.renders_include_worldgen([constants.RENDER_TOP_VIEW])


def test_import_render_registry_without_amulet():
    import importlib

    import renderers.registry as registry_module

    importlib.reload(registry_module)
    assert constants.RENDER_WORLDGEN in registry_module.RENDER_REGISTRY
