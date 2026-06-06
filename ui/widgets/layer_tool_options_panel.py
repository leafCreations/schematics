"""Layer Tool Options Panel (Replaces PaintBrush, Selector, Eraser panels)

This panel uses a QStackedWidget to switch between the options for different layer tools.
It should be integrated into main_window.py's toolbar layout.
"""

from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class LayerToolOptionsPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Layer Tool Options", parent)

        # --- Core Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # --- Placeholder Widgets for Tool Options ---
        self.paint_brush_options = self._create_paint_brush_options()
        self.selector_options = self._create_selector_options()
        self.eraser_options = self._create_eraser_options()

        # Add widgets to the stack
        self.stacked_widget.addWidget(self.paint_brush_options)  # Index 0: Paint Brush
        self.stacked_widget.addWidget(self.selector_options)  # Index 1: Selector
        self.stacked_widget.addWidget(self.eraser_options)  # Index 2: Eraser

        # Set initial visibility/selection if needed, e.g., based on the currently active tool mode
        self.setCurrentToolOptions(0)  # Default to Paint Brush options view

    def _create_paint_brush_options(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Paint Brush Settings:"))
        # Placeholder for brush size slider, flow settings, etc.
        layout.addStretch()
        return widget

    def _create_selector_options(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Selection Settings:"))
        # Placeholder for selection type dropdown, boundary controls, etc.
        layout.addStretch()
        return widget

    def _create_eraser_options(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Eraser Settings:"))
        # Placeholder for erase strength, pattern options, etc.
        layout.addStretch()
        return widget

    def setCurrentToolOptions(self, index: int):
        """Sets the visibility of the correct tool option panel."""
        if 0 <= index < 3:
            self.stacked_widget.setCurrentIndex(index)
