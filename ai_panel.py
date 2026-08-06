"""
ai_panel.py - AI Assistant Floating Sparkle Button & ChatGPT Side Panel.

Provides:
- AIFloatingButton: 52x52px circular floating button with sparkle icon ✦ and drop-shadow pulse effect.
- AISidePanel: 380-420px sliding side panel with 42px header (ChatGPT title & close X button)
  and embedded QWebEngineView loaded with https://chatgpt.com.
- Smooth QPropertyAnimation geometry slide-in/out transitions.
"""

from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,
    QGraphicsDropShadowEffect
)
from PyQt6.QtWebEngineWidgets import QWebEngineView


class AIFloatingButton(QPushButton):
    """
    52x52px circular floating button positioned bottom-center over browser view.
    Features sparkle icon ✦, indigo glass gradient styling, and glowing drop shadow pulse effect.
    """

    def __init__(self, parent=None):
        super().__init__("✦", parent)
        self.setObjectName("AIFloatingButton")
        self.setFixedSize(52, 52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("AI Assistant (ChatGPT)")

        # Animated drop shadow glow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor("#6366f1"))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)

        # Pulse animation for glow effect
        self._pulse_anim = QPropertyAnimation(self.shadow, b"blurRadius", self)
        self._pulse_anim.setDuration(1500)
        self._pulse_anim.setStartValue(10)
        self._pulse_anim.setEndValue(25)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.setLoopCount(-1)  # Indefinite loop
        self._pulse_anim.start()


class AISidePanel(QWidget):
    """
    380-420px (400px default) sliding side panel containing header bar with ChatGPT label,
    close button, and embedded QWebEngineView loaded with https://chatgpt.com.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AISidePanel")
        self.setFixedWidth(400)
        self._is_expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar (42px height)
        self.header_widget = QWidget(self)
        self.header_widget.setObjectName("AIHeader")
        self.header_widget.setFixedHeight(42)

        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(14, 0, 12, 0)
        header_layout.setSpacing(8)

        self.header_label = QLabel("ChatGPT", self.header_widget)
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

        # Embedded QWebEngineView with ChatGPT
        self.webview = QWebEngineView(self)
        self.webview.setObjectName("AIWebEngineView")
        self.webview.setUrl(QUrl("https://chatgpt.com"))
        layout.addWidget(self.webview)

        # Slide animation
        self._anim = QPropertyAnimation(self, b"geometry", self)
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self._on_anim_finished)

        # Hide initially
        self.hide()

    def _on_anim_finished(self):
        """Called when slide animation finishes. Hides widget if collapsing."""
        if not self._is_expanded:
            self.hide()

    def is_expanded(self) -> bool:
        """Return True if panel is expanded, False otherwise."""
        return self._is_expanded

    def isVisible(self) -> bool:
        """Return native QWidget visibility."""
        return super().isVisible()

    def show_panel(self):
        """Slide in / expand the side panel."""
        if self._is_expanded and super().isVisible():
            return

        self._is_expanded = True
        parent = self.parentWidget()
        pw = parent.width() if parent else 1100
        ph = parent.height() if parent else 750
        w = self.width()

        title_bar_h = 0
        if parent and hasattr(parent, "title_bar") and parent.title_bar and parent.title_bar.isVisible():
            title_bar_h = parent.title_bar.height()

        ph_panel = ph - title_bar_h
        end_geom = QRect(pw - w, title_bar_h, w, ph_panel)

        if self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()

        start_geom = self.geometry()
        if start_geom.x() < pw - w or start_geom.x() >= pw:
            start_geom = QRect(pw, title_bar_h, w, ph_panel)

        self.show()
        self.raise_()

        self._anim.setStartValue(start_geom)
        self._anim.setEndValue(end_geom)
        self._anim.start()

    def hide_panel(self):
        """Slide out / collapse the side panel."""
        if not self._is_expanded and not super().isVisible():
            return

        self._is_expanded = False
        parent = self.parentWidget()
        pw = parent.width() if parent else 1100
        ph = parent.height() if parent else 750
        w = self.width()

        title_bar_h = 0
        if parent and hasattr(parent, "title_bar") and parent.title_bar and parent.title_bar.isVisible():
            title_bar_h = parent.title_bar.height()

        ph_panel = ph - title_bar_h
        end_geom = QRect(pw, title_bar_h, w, ph_panel)

        if self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()

        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(end_geom)
        self._anim.start()

    def toggle_panel(self):
        """Toggle side panel expansion state."""
        if self._is_expanded:
            self.hide_panel()
        else:
            self.show_panel()

