import pytest

import helpers.constants as constants
import helpers.pipeline as pipeline


def test_validate_render_names_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown render type"):
        pipeline.validate_render_names({"not_a_renderer"})


def test_validate_render_names_accepts_all_and_known():
    pipeline.validate_render_names({constants.RENDER_ALL, constants.RENDER_TOP_VIEW})


def test_normalize_renders_defaults_to_all():
    assert pipeline.normalize_renders(None) == {constants.RENDER_ALL}
