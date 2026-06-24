import pytest

import helpers.constants as constants
from renderers.registry import PREVIEW_RENDER_REGISTRY
from ui.widgets.render_panel import export_renders_for_preview, worldgen_dependencies_available

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    yield application


def test_worldgen_dependencies_available_is_bool():
    assert isinstance(worldgen_dependencies_available(), bool)


def test_export_renders_for_preview_maps_preview_key():
    for render_name in PREVIEW_RENDER_REGISTRY:
        assert export_renders_for_preview(render_name) == [render_name]


def test_export_renders_for_preview_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown preview render"):
        export_renders_for_preview("not_a_render")


def test_export_renders_for_preview_top_down():
    assert export_renders_for_preview(constants.RENDER_TOP_VIEW) == [constants.RENDER_TOP_VIEW]


def test_render_panel_disables_generate_world_without_template(qapp, monkeypatch):
    from ui.widgets.render_panel import RenderPanel

    monkeypatch.setattr(
        "ui.widgets.render_panel.worldgen_dependencies_available",
        lambda: True,
    )
    panel = RenderPanel()
    panel.set_worldgen_template_available(False)
    assert panel._generate_world_button.isEnabled() is False
    assert "worldgen template" in panel._generate_world_button.toolTip().lower()

    panel.set_worldgen_template_available(True)
    assert panel._generate_world_button.isEnabled() is True


def test_render_panel_has_export_and_world_buttons(qapp):
    from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QToolButton

    from ui.widgets.render_panel import RenderPanel

    panel = RenderPanel()
    assert panel._export_button.text() == "Export Render"
    assert isinstance(panel._export_button, QToolButton)
    assert panel._export_button.menu() is not None
    assert panel._export_button.menu().actions()[0].text() == "All Renders"
    assert panel._generate_world_button.text() == "Generate World"
    assert panel._open_output_button.text() == "Open Output Folder"
    assert panel._export_button.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Maximum
    assert (
        panel._generate_world_button.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Maximum
    )
    assert panel._open_output_button.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Maximum

    actions_layout = panel._open_output_button.parentWidget().layout()
    assert isinstance(actions_layout, QHBoxLayout)
    assert actions_layout.indexOf(panel._export_button) >= 0
    assert actions_layout.indexOf(panel._generate_world_button) >= 0
    assert actions_layout.indexOf(panel._open_output_button) >= 0
