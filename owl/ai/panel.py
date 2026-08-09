"""
ai_panel.py - Ask Owl floating pill & docked (push) side panel.

AISidePanel docks in the content row and pushes the page left — not an overlay.
"""

from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve, QVariantAnimation, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,
    QGraphicsDropShadowEffect, QSizePolicy,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

ASK_OWL_WIDTH = 128
ASK_OWL_HEIGHT = 40
PANEL_WIDTH = 400


class AIFloatingButton(QPushButton):
    """Bottom-center Gemini-style pill: "✦ Ask Owl"."""

    def __init__(self, parent=None):
        super().__init__("✦  Ask Owl", parent)
        self.setObjectName("AIFloatingButton")
        self.setFixedSize(ASK_OWL_WIDTH, ASK_OWL_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Ask Owl (AI Assistant)")

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(18)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        self.shadow.setOffset(0, 2)
        self.setGraphicsEffect(self.shadow)

        self._pulse_anim = QPropertyAnimation(self.shadow, b"blurRadius", self)
        self._pulse_anim.setDuration(1800)
        self._pulse_anim.setStartValue(12)
        self._pulse_anim.setEndValue(22)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.start()


class AISidePanel(QWidget):
    """
    Docked side panel that pushes page content (sidebar layout).

    Width animates 0 ↔ PANEL_WIDTH inside a horizontal content layout.
    """

    expanded_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AISidePanel")
        self._is_expanded = False
        self._panel_width = PANEL_WIDTH

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(0)
        self.setMaximumWidth(self._panel_width)
        self.setFixedWidth(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header_widget = QWidget(self)
        self.header_widget.setObjectName("AIHeader")
        self.header_widget.setFixedHeight(42)

        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(14, 0, 12, 0)
        header_layout.setSpacing(8)

        self.header_label = QLabel("Ask Owl", self.header_widget)
        self.header_label.setObjectName("AIHeaderLabel")

        self.close_btn = QPushButton("✕", self.header_widget)
        self.close_btn.setObjectName("AICloseBtn")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.hide_panel)

        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)

        layout.addWidget(self.header_widget)

        self.webview = QWebEngineView(self)
        self.webview.setObjectName("AIWebEngineView")
        self.webview.setUrl(QUrl("https://chatgpt.com"))
        layout.addWidget(self.webview, 1)

        # Width animation for push/dock behavior
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_width_anim)
        self._anim.finished.connect(self._on_anim_finished)

        self.hide()

    def _on_width_anim(self, value):
        w = int(value)
        self.setFixedWidth(w)
        self.setMaximumWidth(max(w, 1) if w > 0 else self._panel_width)

    def _on_anim_finished(self):
        if not self._is_expanded:
            self.setFixedWidth(0)
            self.hide()
        else:
            self.setFixedWidth(self._panel_width)
        self.expanded_changed.emit(self._is_expanded)

    def is_expanded(self) -> bool:
        return self._is_expanded

    def isVisible(self) -> bool:
        return super().isVisible()

    def show_panel(self):
        if self._is_expanded and super().isVisible() and self.width() >= self._panel_width - 2:
            return

        self._is_expanded = True
        self.show()
        self.raise_()

        if self._anim.state() == QVariantAnimation.State.Running:
            self._anim.stop()

        start = self.width()
        self._anim.setStartValue(start)
        self._anim.setEndValue(self._panel_width)
        self._anim.start()
        self.expanded_changed.emit(True)

    def hide_panel(self):
        if not self._is_expanded and not super().isVisible():
            return

        self._is_expanded = False

        if self._anim.state() == QVariantAnimation.State.Running:
            self._anim.stop()

        if not super().isVisible():
            self.setFixedWidth(0)
            self.expanded_changed.emit(False)
            return

        self.show()
        self._anim.setStartValue(self.width() if self.width() > 0 else self._panel_width)
        self._anim.setEndValue(0)
        self._anim.start()
        self.expanded_changed.emit(False)

    def toggle_panel(self):
        if self._is_expanded:
            self.hide_panel()
        else:
            self.show_panel()
