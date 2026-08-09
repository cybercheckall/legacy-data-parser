"""
Owl window handler row (frameless shell L1).

Traffic lights · owl logo (no wordmark) · tabs host · stealth status.
Navigation / URL live in NavBar directly beneath (L2).
"""

from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QMouseEvent, QIcon
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSlider, QSizePolicy,
)

from owl.design.icons import owl_logo_pixmap, icon_shield


class CommandBar(QWidget):
    """Handler row: brand icon + tabs slot + stealth + window controls."""

    shield_requested = pyqtSignal()
    home_requested = pyqtSignal()

    def __init__(self, parent=None, title: str = "Owl"):
        super().__init__(parent)
        self.setObjectName("CommandBar")
        self.setFixedHeight(38)
        self._drag_pos = None
        self._title = title

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(6)

        # macOS-style traffic lights (left)
        self.close_btn = self._traffic("CloseButton", "#ff5f57", "Close", self._on_close)
        self.min_btn = self._traffic("MinButton", "#febc2e", "Minimize", self._on_minimize)
        self.max_btn = self._traffic("MaxButton", "#28c840", "Maximize / Restore", self._toggle_maximize)
        layout.addWidget(self.close_btn)
        layout.addWidget(self.min_btn)
        layout.addWidget(self.max_btn)

        layout.addSpacing(6)

        # Owl logo only — no wordmark
        logo = owl_logo_pixmap(20)
        self.owl_btn = QPushButton(self)
        self.owl_btn.setObjectName("OwlBrandBtn")
        self.owl_btn.setFixedSize(28, 28)
        self.owl_btn.setIcon(QIcon(logo))
        self.owl_btn.setIconSize(logo.size())
        self.owl_btn.setToolTip("Owl")
        self.owl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.owl_btn.clicked.connect(self.home_requested.emit)
        layout.addWidget(self.owl_btn)

        # Compatibility: hidden title label (icon-only shell)
        self.title_label = QLabel("", self)
        self.title_label.setObjectName("TitleLabel")
        self.title_label.hide()

        self.tabs_host = QWidget(self)
        self.tabs_host.setObjectName("HandlerTabsHost")
        self.tabs_host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._tabs_layout = QHBoxLayout(self.tabs_host)
        self._tabs_layout.setContentsMargins(0, 0, 0, 0)
        self._tabs_layout.setSpacing(0)
        layout.addWidget(self.tabs_host, 1)

        self.shield_btn = QPushButton(self)
        self.shield_btn.setObjectName("ShieldBtn")
        self.shield_btn.setProperty("class", "NavButton")
        self.shield_btn.setFixedSize(28, 28)
        self.shield_btn.setIcon(icon_shield(16))
        self.shield_btn.setIconSize(QSize(16, 16))
        self.shield_btn.setToolTip("Shields · Ephemeral · Hidden from capture")
        self.shield_btn.clicked.connect(self.shield_requested.emit)
        layout.addWidget(self.shield_btn)

        # Ghost opacity — handler-right, next to shield (stealth control)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.opacity_slider.setObjectName("OpacitySlider")
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setFixedSize(72, 20)
        self.opacity_slider.setToolTip("Window opacity · 10% – 100%")
        self.opacity_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        layout.addWidget(self.opacity_slider)

    def set_tabs_widget(self, widget: QWidget):
        """Embed the tab strip into the handler row."""
        while self._tabs_layout.count():
            item = self._tabs_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        if widget is not None:
            widget.setParent(self.tabs_host)
            self._tabs_layout.addWidget(widget, 1)

    def _traffic(self, object_name, color, tip, slot):
        btn = QPushButton("", self)
        btn.setObjectName(object_name)
        btn.setProperty("class", "TrafficLight")
        btn.setFixedSize(12, 12)
        btn.setToolTip(tip)
        btn.setStyleSheet(
            f"QPushButton#{object_name} {{"
            f"background-color: {color}; border: none; border-radius: 6px; min-width: 12px; max-width: 12px;"
            f"min-height: 12px; max-height: 12px; padding: 0; }}"
        )
        btn.clicked.connect(slot)
        return btn

    def set_title(self, text: str):
        """API compat — shell is icon-only."""
        self._title = text or "Owl"
        self.title_label.setText("")
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

    def _is_interactive_target(self, pos) -> bool:
        for w in (
            self.close_btn, self.min_btn, self.max_btn, self.owl_btn,
            self.shield_btn, self.opacity_slider, self.tabs_host,
        ):
            if w.geometry().contains(pos):
                return True
        return False

    def mousePressEvent(self, event: QMouseEvent):
        if self._is_interactive_target(event.position().toPoint()):
            event.ignore()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win and not win.isMaximized():
                self._drag_pos = event.globalPosition().toPoint() - win.frameGeometry().topLeft()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            win = self.window()
            if win and not win.isMaximized():
                win.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and not self._is_interactive_target(event.position().toPoint()):
            self._toggle_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
