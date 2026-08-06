"""
title_bar.py - Frameless Dark Glass TitleBar Widget.

Provides frameless window drag support, window control buttons (min, max, close),
double-click toggle maximize, and window title label.
"""

from PyQt6.QtCore import Qt, QPoint, QEvent
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSlider


class TitleBar(QWidget):
    """Custom frameless dark glass TitleBar widget."""

    def __init__(self, parent=None, title: str = "🦉 Owl"):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(34)

        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(6)

        # Title label
        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("TitleLabel")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Window Opacity Slider (M2)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.opacity_slider.setObjectName("OpacitySlider")
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setToolTip("Window Opacity (10% - 100%)")
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        layout.addWidget(self.opacity_slider)

        # Minimize button
        self.min_btn = QPushButton("—", self)
        self.min_btn.setObjectName("MinButton")
        self.min_btn.setProperty("class", "TitleButton")
        self.min_btn.setFixedSize(30, 24)
        self.min_btn.setToolTip("Minimize")
        self.min_btn.clicked.connect(self._on_minimize)
        layout.addWidget(self.min_btn)

        # Maximize / Restore button
        self.max_btn = QPushButton("□", self)
        self.max_btn.setObjectName("MaxButton")
        self.max_btn.setProperty("class", "TitleButton")
        self.max_btn.setFixedSize(30, 24)
        self.max_btn.setToolTip("Maximize / Restore")
        self.max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.max_btn)

        # Close button
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setProperty("class", "TitleButton")
        self.close_btn.setFixedSize(30, 24)
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self._on_close)
        layout.addWidget(self.close_btn)

    def set_title(self, text: str):
        """Update title label text."""
        self.title_label.setText(text)

    def _on_opacity_changed(self, value: int):
        """Update window opacity when opacity slider value changes."""
        win = self.window()
        if win and hasattr(win, "setWindowOpacity"):
            win.setWindowOpacity(value / 100.0)

    def _on_minimize(self):
        win = self.window()
        if win and hasattr(win, "showMinimized"):
            win.showMinimized()

    def _on_close(self):
        win = self.window()
        if win and hasattr(win, "close"):
            win.close()

    def _toggle_maximize(self):
        win = self.window()
        if not win:
            return
        if hasattr(win, "_toggle_maximize") and callable(win._toggle_maximize):
            win._toggle_maximize()
            if win.isMaximized():
                self.max_btn.setText("❐")
            else:
                self.max_btn.setText("□")
        elif hasattr(win, "isMaximized"):
            if win.isMaximized():
                win.showNormal()
                self.max_btn.setText("□")
            else:
                win.showMaximized()
                self.max_btn.setText("❐")

    def mousePressEvent(self, event: QMouseEvent):
        if hasattr(self, "opacity_slider") and self.opacity_slider.geometry().contains(event.position().toPoint()):
            event.ignore()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win and not win.isMaximized():
                self._drag_pos = event.globalPosition().toPoint() - win.frameGeometry().topLeft()
                event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            win = self.window()
            if win and not win.isMaximized():
                win.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
