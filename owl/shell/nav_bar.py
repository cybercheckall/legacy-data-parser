"""
nav_bar.py - Slim place row under the window handler.

Crisp icon nav + pill omnibox with trailing bookmark action.
"""

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QSizePolicy

from owl.design.icons import (
    icon_back, icon_forward, icon_reload, icon_star, icon_shield, icon_menu, icon_size,
)


class NavBar(QWidget):
    """Toolbar under the tab/handler strip."""

    navigate_requested = pyqtSignal(str)
    refresh_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    profile_requested = pyqtSignal()
    back_requested = pyqtSignal()
    forward_requested = pyqtSignal()
    shield_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NavBar")
        self.setFixedHeight(42)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(4)

        self.back_btn = self._icon_btn("BackBtn", icon_back(), "Back", self.back_requested)
        self.fwd_btn = self._icon_btn("FwdBtn", icon_forward(), "Forward", self.forward_requested)
        self.reload_btn = self._icon_btn("ReloadBtn", icon_reload(), "Reload page", self.refresh_requested)
        layout.addWidget(self.back_btn)
        layout.addWidget(self.fwd_btn)
        layout.addWidget(self.reload_btn)

        layout.addSpacing(8)

        self.url_bar = QLineEdit(self)
        self.url_bar.setObjectName("NavUrlBar")
        self.url_bar.setPlaceholderText("Search or paste a private URL")
        self.url_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.url_bar.returnPressed.connect(self._on_return_pressed)

        # Bookmark lives inside the omnibox (cleaner than a loose icon beside it)
        self._bookmark_action = QAction(icon_star(), "Bookmark", self.url_bar)
        self._bookmark_action.setToolTip("Bookmark this tab")
        self.url_bar.addAction(self._bookmark_action, QLineEdit.ActionPosition.TrailingPosition)
        self.bookmark_btn = self._bookmark_action  # compat alias

        layout.addWidget(self.url_bar, 1)

        layout.addSpacing(4)

        # Trailing utility cluster
        self.shield_btn = self._icon_btn(
            "ShieldBtn", icon_shield(), "Shields · Ephemeral session", self.shield_requested
        )
        layout.addWidget(self.shield_btn)

        self.profile_btn = QPushButton(self)
        self.profile_btn.setObjectName("ProfileBtn")
        self.profile_btn.setProperty("class", "NavButton")
        self.profile_btn.setFixedSize(32, 32)
        self.profile_btn.setToolTip("Switch Profile")
        self.profile_btn.setText("👤")
        self.profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.profile_btn.clicked.connect(self.profile_requested.emit)
        layout.addWidget(self.profile_btn)

        self.settings_btn = self._icon_btn(
            "SettingsBtn", icon_menu(), "Customize and control Owl", self.settings_requested
        )
        layout.addWidget(self.settings_btn)

    def _icon_btn(self, object_name, icon, tip, signal):
        btn = QPushButton(self)
        btn.setObjectName(object_name)
        btn.setProperty("class", "NavButton")
        btn.setFixedSize(32, 32)
        btn.setIcon(icon)
        btn.setIconSize(icon_size())
        btn.setText("")
        btn.setToolTip(tip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFlat(True)
        if signal is not None:
            btn.clicked.connect(signal.emit)
        return btn

    def _on_return_pressed(self):
        self.navigate_requested.emit(self.url_bar.text())

    def set_url(self, url_str: str):
        self.url_bar.blockSignals(True)
        self.url_bar.setText(url_str)
        self.url_bar.blockSignals(False)

    def set_profile_avatar(self, avatar: str):
        self.profile_btn.setIcon(QIcon())
        self.profile_btn.setText(avatar or "👤")
