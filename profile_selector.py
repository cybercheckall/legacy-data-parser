"""
profile_selector.py - Modern Card-Based Profile Selector Screen.

Provides card-based profile selection UI on application startup and profile switching,
rendering profile cards with avatars, homepages, and search engine badges.
"""

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor, QFont

from profile_manager import Profile


class ProfileSelector(QWidget):
    """Card-based profile selector view/overlay widget."""

    profile_selected = pyqtSignal(object)  # Emits Profile object

    def __init__(self, profiles=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ProfileSelector")
        self.profiles = profiles or []
        self.cards = []  # List of clickable card buttons for test contract compatibility
        self.cards_layout = None

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Header Title
        title = QLabel("🦉 Owl", self)
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #f8fafc; background: transparent; margin-bottom: 4px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Select a profile to launch your private ephemeral workspace", self)
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px; background: transparent; margin-bottom: 30px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        # Grid for profile cards
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(20)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addLayout(self.cards_layout)
        main_layout.addStretch()

        self._populate_cards()

    def _populate_cards(self):
        """Instantiate card buttons for active profiles and add to cards_layout."""
        for p in self.profiles:
            card_btn = self._create_profile_card(p)
            if self.cards_layout:
                self.cards_layout.addWidget(card_btn)
            self.cards.append(card_btn)

    def _create_profile_card(self, profile: Profile) -> QPushButton:
        """Create a styled card button representing a browser profile."""
        card_text = f"{profile.avatar}\n\n{profile.name}\n({profile.search_engine})"
        card_btn = QPushButton(card_text, self)
        card_btn.setProperty("class", "ProfileCard")
        card_btn.setFixedSize(200, 160)
        card_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        card_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: rgba(30, 41, 59, 0.80);
                color: #f8fafc;
                border: 2px solid rgba(255, 255, 255, 0.10);
                border-radius: 16px;
                padding: 16px;
                font-size: 15px;
                font-weight: bold;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: rgba(51, 65, 85, 0.95);
                border: 2px solid {profile.theme_color or '#6366f1'};
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background-color: #6366f1;
            }}
            """
        )
        card_btn.clicked.connect(lambda _, prof=profile: self._on_card_clicked(prof))
        return card_btn

    def _on_card_clicked(self, profile: Profile):
        self.profile_selected.emit(profile)

    def set_profiles(self, profiles):
        """Update list of profiles and rebuild UI cards cleanly without re-creating layout."""
        self.profiles = profiles or []
        for card in self.cards:
            if self.cards_layout:
                self.cards_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()
        self._populate_cards()

