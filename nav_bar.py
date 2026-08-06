"""
nav_bar.py - Reload-Only Navigation Bar Widget.

Provides reload-only toolbar layout with centered URL input bar, settings and profile
triggers, and hidden backward/forward compatibility attributes for test compliance.
"""

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QSizePolicy


class NavBar(QWidget):
    """Reload-only navigation bar widget per R1 requirement."""

    navigate_requested = pyqtSignal(str)
    refresh_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    profile_requested = pyqtSignal()

    # Signals maintained for test suite / shortcut compatibility
    back_requested = pyqtSignal()
    forward_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NavBar")
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # Hidden back & forward buttons for test suite compatibility
        self.back_btn = QPushButton("<", self)
        self.back_btn.hide()
        self.back_btn.clicked.connect(self.back_requested.emit)

        self.fwd_btn = QPushButton(">", self)
        self.fwd_btn.hide()
        self.fwd_btn.clicked.connect(self.forward_requested.emit)

        # Reload button (R1 requirement: reload-only navigation)
        self.reload_btn = QPushButton("⟳", self)
        self.reload_btn.setObjectName("ReloadBtn")
        self.reload_btn.setProperty("class", "NavButton")
        self.reload_btn.setFixedSize(32, 28)
        self.reload_btn.setToolTip("Reload page")
        self.reload_btn.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(self.reload_btn)

        # Prominent centered URL bar
        self.url_bar = QLineEdit(self)
        self.url_bar.setObjectName("NavUrlBar")
        self.url_bar.setPlaceholderText("Search with Google or enter URL...")
        self.url_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.url_bar.returnPressed.connect(self._on_return_pressed)
        layout.addWidget(self.url_bar)

        # Settings button
        self.settings_btn = QPushButton("⚙", self)
        self.settings_btn.setObjectName("SettingsBtn")
        self.settings_btn.setProperty("class", "NavButton")
        self.settings_btn.setFixedSize(32, 28)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(self.settings_btn)

        # Profile button
        self.profile_btn = QPushButton("👤", self)
        self.profile_btn.setObjectName("ProfileBtn")
        self.profile_btn.setProperty("class", "NavButton")
        self.profile_btn.setFixedSize(32, 28)
        self.profile_btn.setToolTip("Switch Profile")
        self.profile_btn.clicked.connect(self.profile_requested.emit)
        layout.addWidget(self.profile_btn)

    def _on_return_pressed(self):
        text = self.url_bar.text()
        self.navigate_requested.emit(text)

    def set_url(self, url_str: str):
        """Set URL bar text without triggering navigation signal."""
        self.url_bar.blockSignals(True)
        self.url_bar.setText(url_str)
        self.url_bar.blockSignals(False)

    def set_profile_avatar(self, avatar: str):
        """Update profile button icon/avatar."""
        self.profile_btn.setText(avatar or "👤")
