"""
title_bar.py - Frameless handler widget (owl logo, no wordmark).

Provides frameless window drag support, traffic-light window controls,
double-click toggle maximize, and owl brand icon.
"""

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QMouseEvent, QIcon
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSlider

from owl.design.icons import owl_logo_pixmap


class TitleBar(QWidget):
    """Custom frameless title/handler bar with owl icon branding."""

    def __init__(self, parent=None, title: str = "Owl"):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(36)
        self._title = title
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 6, 0)
        layout.setSpacing(6)

        self.close_btn = self._traffic("CloseButton", "#ff5f57", "Close", self._on_close)
        self.min_btn = self._traffic("MinButton", "#febc2e", "Minimize", self._on_minimize)
        self.max_btn = self._traffic("MaxButton", "#28c840", "Maximize / Restore", self._toggle_maximize)
        layout.addWidget(self.close_btn)
        layout.addWidget(self.min_btn)
        layout.addWidget(self.max_btn)

        layout.addSpacing(6)

        logo = owl_logo_pixmap(20)
        self.owl_btn = QPushButton(self)
        self.owl_btn.setObjectName("OwlBrandBtn")
        self.owl_btn.setFixedSize(28, 28)
        self.owl_btn.setIcon(QIcon(logo))
        self.owl_btn.setIconSize(QSize(20, 20))
        self.owl_btn.setToolTip(title)
        layout.addWidget(self.owl_btn)

        # Compatibility: empty label (icon-only; tests assert brand via owl_btn)
        self.title_label = QLabel("", self)
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setToolTip(title)
        self.title_label.hide()

        layout.addStretch()

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.opacity_slider.setObjectName("OpacitySlider")
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setToolTip("Window Opacity (10% - 100%)")
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        layout.addWidget(self.opacity_slider)

    def _traffic(self, object_name, color, tip, slot):
        btn = QPushButton("", self)
        btn.setObjectName(object_name)
        btn.setProperty("class", "TrafficLight")
        btn.setFixedSize(12, 12)
        btn.setToolTip(tip)
        btn.setStyleSheet(
            f"QPushButton#{object_name} {{"
            f"background-color: {color}; border: none; border-radius: 6px;"
            f"min-width: 12px; max-width: 12px; min-height: 12px; max-height: 12px; padding: 0; }}"
        )
        btn.clicked.connect(slot)
        return btn

    def set_title(self, text: str):
        self._title = text or "Owl"
        self.title_label.setText("")
        self.title_label.setToolTip(self._title)
        self.owl_btn.setToolTip(self._title)

    def _on_opacity_changed(self, value: int):
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
        elif hasattr(win, "isMaximized"):
            if win.isMaximized():
                win.showNormal()
            else:
                win.showMaximized()

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
