from PySide6.QtWidgets import QApplication

from ui.widgets.worldgen_version_dialog import WorldgenVersionDialog


def test_worldgen_version_dialog_defaults_to_preferred_version():
    application = QApplication.instance() or QApplication([])

    dialog = WorldgenVersionDialog(None, versions=["26.1.2", "26.2"], default_version="26.2")
    assert dialog.selected_version() == "26.2"

    application.processEvents()
