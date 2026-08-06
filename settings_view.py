"""
settings_view.py - Modern Glassmorphic Settings View & Search Engine Switcher.

Provides SettingsView widget featuring sidebar navigation (General, Profiles,
Search Engine, Appearance, About), search engine preference selector (Google vs DuckDuckGo),
profile CRUD manager, homepage configuration editor, and dark glassmorphic styling.
"""

import logging
from typing import Optional

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QLineEdit, QStackedWidget, QRadioButton, QComboBox,
    QGroupBox, QFormLayout, QMessageBox, QFrame
)

from profile_manager import ProfileManager, Profile, VALID_SEARCH_ENGINES

logger = logging.getLogger(__name__)


class SettingsView(QWidget):
    """
    Modern dark glassmorphic Settings View with sidebar navigation.
    
    Emits:
    - search_engine_changed(str): Emitted when default search engine changes.
    - profile_updated(): Emitted when profile CRUD operations complete.
    - homepage_changed(str): Emitted when homepage URL setting changes.
    """

    search_engine_changed = pyqtSignal(str)
    profile_updated = pyqtSignal()
    homepage_changed = pyqtSignal(str)

    def __init__(self, profile_manager: Optional[ProfileManager] = None, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsView")
        self.profile_manager = profile_manager or ProfileManager()

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # --- Sidebar Navigation ---
        self.sidebar = QWidget(self)
        self.sidebar.setObjectName("SettingsSidebar")
        self.sidebar.setFixedWidth(200)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(6)

        sidebar_title = QLabel("Settings", self.sidebar)
        sidebar_title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 6px; color: #f8fafc;")
        sidebar_layout.addWidget(sidebar_title)

        self.btn_general = QPushButton("⚙ General", self.sidebar)
        self.btn_general.setProperty("class", "SettingsNavBtn")
        self.btn_general.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_profiles = QPushButton("👤 Profiles", self.sidebar)
        self.btn_profiles.setProperty("class", "SettingsNavBtn")
        self.btn_profiles.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_search = QPushButton("🔍 Search Engine", self.sidebar)
        self.btn_search.setProperty("class", "SettingsNavBtn")
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_appearance = QPushButton("🎨 Appearance", self.sidebar)
        self.btn_appearance.setProperty("class", "SettingsNavBtn")
        self.btn_appearance.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_about = QPushButton("ℹ About", self.sidebar)
        self.btn_about.setProperty("class", "SettingsNavBtn")
        self.btn_about.setCursor(Qt.CursorShape.PointingHandCursor)

        self.nav_buttons = [
            self.btn_general,
            self.btn_profiles,
            self.btn_search,
            self.btn_appearance,
            self.btn_about,
        ]

        for btn in self.nav_buttons:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        main_layout.addWidget(self.sidebar)

        # --- Right Stack Container ---
        self.stack = QStackedWidget(self)
        self.stack.setObjectName("SettingsStack")
        main_layout.addWidget(self.stack)

        # Build individual section pages
        self._build_general_page()
        self._build_profiles_page()
        self._build_search_page()
        self._build_appearance_page()
        self._build_about_page()

        # Connect sidebar buttons to stack pages
        self.btn_general.clicked.connect(lambda: self._switch_section(0))
        self.btn_profiles.clicked.connect(lambda: self._switch_section(1))
        self.btn_search.clicked.connect(lambda: self._switch_section(2))
        self.btn_appearance.clicked.connect(lambda: self._switch_section(3))
        self.btn_about.clicked.connect(lambda: self._switch_section(4))

        self._switch_section(0)

    def _switch_section(self, index: int):
        """Switch active stack page and update sidebar button highlight states."""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            active = (i == index)
            btn.setProperty("active", "true" if active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # --- Page 0: General ---

    def _build_general_page(self):
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("General Settings", page)
        title.setProperty("class", "SettingsTitle")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(title)

        subtitle = QLabel("Configure startup behavior and homepage preferences", page)
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px; margin-bottom: 12px;")
        layout.addWidget(subtitle)

        # Homepage Section Card
        card = QFrame(page)
        card.setProperty("class", "SettingsCard")
        card_layout = QVBoxLayout(card)

        card_title = QLabel("Homepage URL", card)
        card_title.setStyleSheet("font-weight: bold; color: #f8fafc;")
        card_layout.addWidget(card_title)

        active_prof = self.profile_manager.get_active_profile()
        self.homepage_input = QLineEdit(active_prof.homepage if active_prof else "https://www.google.com", card)
        self.homepage_input.setObjectName("HomepageInput")
        self.homepage_input.setPlaceholderText("Enter homepage URL (e.g. https://www.google.com)")
        self.homepage_input.returnPressed.connect(self._on_save_homepage)
        card_layout.addWidget(self.homepage_input)

        save_hp_btn = QPushButton("Save Homepage", card)
        save_hp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_hp_btn.clicked.connect(self._on_save_homepage)
        card_layout.addWidget(save_hp_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(card)
        layout.addStretch()
        self.stack.addWidget(page)

    def _on_save_homepage(self):
        url = self.homepage_input.text()
        self.set_homepage(url)

    # --- Page 1: Profiles ---

    def _build_profiles_page(self):
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Profile Management", page)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(title)

        subtitle = QLabel("Manage ephemeral off-the-record browser profiles", page)
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px; margin-bottom: 12px;")
        layout.addWidget(subtitle)

        # Profile Switcher / Editor Card
        card = QFrame(page)
        card.setProperty("class", "SettingsCard")
        card_layout = QVBoxLayout(card)

        card_title = QLabel("Active Profile Settings", card)
        card_title.setStyleSheet("font-weight: bold; color: #f8fafc;")
        card_layout.addWidget(card_title)

        form_layout = QFormLayout()

        self.prof_select_combo = QComboBox(card)
        self._refresh_profile_combo()
        self.prof_select_combo.currentIndexChanged.connect(self._on_profile_selected_combo)
        form_layout.addRow("Select Profile:", self.prof_select_combo)

        self.prof_name_input = QLineEdit(card)
        form_layout.addRow("Profile Name:", self.prof_name_input)

        self.prof_avatar_input = QLineEdit(card)
        form_layout.addRow("Avatar Icon:", self.prof_avatar_input)

        self.prof_hp_input = QLineEdit(card)
        form_layout.addRow("Homepage:", self.prof_hp_input)

        self.prof_engine_combo = QComboBox(card)
        self.prof_engine_combo.addItems(VALID_SEARCH_ENGINES)
        form_layout.addRow("Search Engine:", self.prof_engine_combo)

        card_layout.addLayout(form_layout)

        btn_box = QHBoxLayout()

        save_prof_btn = QPushButton("Save Changes", card)
        save_prof_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_prof_btn.clicked.connect(self._on_save_active_profile)
        btn_box.addWidget(save_prof_btn)

        set_active_btn = QPushButton("Make Active", card)
        set_active_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        set_active_btn.clicked.connect(self._on_set_active_profile_clicked)
        btn_box.addWidget(set_active_btn)

        delete_prof_btn = QPushButton("Delete Profile", card)
        delete_prof_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_prof_btn.setStyleSheet("background-color: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444;")
        delete_prof_btn.clicked.connect(self._on_delete_profile_clicked)
        btn_box.addWidget(delete_prof_btn)

        card_layout.addLayout(btn_box)
        layout.addWidget(card)

        # Create New Profile Card
        new_card = QFrame(page)
        new_card.setProperty("class", "SettingsCard")
        new_layout = QVBoxLayout(new_card)

        new_title = QLabel("Create New Profile", new_card)
        new_title.setStyleSheet("font-weight: bold; color: #f8fafc;")
        new_layout.addWidget(new_title)

        new_form = QFormLayout()

        self.new_prof_name = QLineEdit(new_card)
        self.new_prof_name.setPlaceholderText("e.g. Work / Research")
        new_form.addRow("Name:", self.new_prof_name)

        self.new_prof_avatar = QLineEdit("💼", new_card)
        new_form.addRow("Avatar:", self.new_prof_avatar)

        self.new_prof_hp = QLineEdit("https://www.google.com", new_card)
        new_form.addRow("Homepage:", self.new_prof_hp)

        self.new_prof_engine = QComboBox(new_card)
        self.new_prof_engine.addItems(VALID_SEARCH_ENGINES)
        new_form.addRow("Search Engine:", self.new_prof_engine)

        new_layout.addLayout(new_form)

        create_btn = QPushButton("Create Profile", new_card)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._on_create_profile_clicked)
        new_layout.addWidget(create_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(new_card)
        layout.addStretch()

        self._populate_active_profile_fields()
        self.stack.addWidget(page)

    def _refresh_profile_combo(self):
        self.prof_select_combo.blockSignals(True)
        self.prof_select_combo.clear()
        profiles = self.profile_manager.load_profiles()
        active = self.profile_manager.get_active_profile()
        active_idx = 0
        for i, p in enumerate(profiles):
            label = f"{p.avatar} {p.name}" + (" (Active)" if active and p.id == active.id else "")
            self.prof_select_combo.addItem(label, p.id)
            if active and p.id == active.id:
                active_idx = i
        self.prof_select_combo.setCurrentIndex(active_idx)
        self.prof_select_combo.blockSignals(False)

    def _populate_active_profile_fields(self):
        selected_id = self.prof_select_combo.currentData()
        if not selected_id:
            active = self.profile_manager.get_active_profile()
            selected_id = active.id if active else None

        prof = self.profile_manager.get_profile_by_id(selected_id) if selected_id else self.profile_manager.get_active_profile()
        if prof:
            self.prof_name_input.setText(prof.name)
            self.prof_avatar_input.setText(prof.avatar)
            self.prof_hp_input.setText(prof.homepage)
            idx = self.prof_engine_combo.findText(prof.search_engine)
            if idx >= 0:
                self.prof_engine_combo.setCurrentIndex(idx)

    def _on_profile_selected_combo(self, index: int):
        self._populate_active_profile_fields()

    def _sync_sub_pages(self):
        """Synchronize controls across sub-pages (Search Engine radios, General Homepage input, Profiles combo/fields)."""
        active = self.profile_manager.get_active_profile()
        if not active:
            return

        # Sync Page 0 (General Homepage input)
        if hasattr(self, "homepage_input"):
            self.homepage_input.blockSignals(True)
            self.homepage_input.setText(active.homepage)
            self.homepage_input.blockSignals(False)

        # Sync Page 2 (Search Engine radio buttons)
        if hasattr(self, "radio_google") and hasattr(self, "radio_ddg"):
            self.radio_google.blockSignals(True)
            self.radio_ddg.blockSignals(True)
            if active.search_engine == "DuckDuckGo":
                self.radio_ddg.setChecked(True)
                self.radio_google.setChecked(False)
            else:
                self.radio_google.setChecked(True)
                self.radio_ddg.setChecked(False)
            self.radio_google.blockSignals(False)
            self.radio_ddg.blockSignals(False)

    def _on_save_active_profile(self):
        pid = self.prof_select_combo.currentData()
        if pid:
            self.profile_manager.update_profile(
                pid,
                name=self.prof_name_input.text(),
                avatar=self.prof_avatar_input.text(),
                homepage=self.prof_hp_input.text(),
                search_engine=self.prof_engine_combo.currentText()
            )
            self._refresh_profile_combo()
            self._sync_sub_pages()
            self.profile_updated.emit()

    def _on_set_active_profile_clicked(self):
        pid = self.prof_select_combo.currentData()
        if pid:
            self.profile_manager.set_active_profile(pid)
            self._refresh_profile_combo()
            self._populate_active_profile_fields()
            self._sync_sub_pages()
            self.profile_updated.emit()

    def _on_create_profile_clicked(self):
        name = self.new_prof_name.text().strip() or "New Profile"
        avatar = self.new_prof_avatar.text().strip() or "👤"
        hp = self.new_prof_hp.text().strip() or "https://www.google.com"
        engine = self.new_prof_engine.currentText()

        prof = self.profile_manager.create_profile(name, avatar=avatar, homepage=hp, search_engine=engine)
        if prof:
            self._refresh_profile_combo()
            self.new_prof_name.clear()
            self._sync_sub_pages()
            self.profile_updated.emit()

    def _on_delete_profile_clicked(self):
        pid = self.prof_select_combo.currentData()
        if pid:
            success = self.profile_manager.delete_profile(pid)
            if success:
                self._refresh_profile_combo()
                self._populate_active_profile_fields()
                self._sync_sub_pages()
                self.profile_updated.emit()
            else:
                logger.warning("Cannot delete profile: at least one profile is required.")

    # --- Page 2: Search Engine ---

    def _build_search_page(self):
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Search Engine Switcher", page)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(title)

        subtitle = QLabel("Select your preferred default search engine for omnibox queries", page)
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px; margin-bottom: 12px;")
        layout.addWidget(subtitle)

        card = QFrame(page)
        card.setProperty("class", "SettingsCard")
        card_layout = QVBoxLayout(card)

        active = self.profile_manager.get_active_profile()
        current_engine = active.search_engine if active else "Google"

        self.radio_google = QRadioButton("Google", card)
        self.radio_google.setObjectName("RadioGoogle")
        self.radio_google.setCursor(Qt.CursorShape.PointingHandCursor)

        self.radio_ddg = QRadioButton("DuckDuckGo", card)
        self.radio_ddg.setObjectName("RadioDuckDuckGo")
        self.radio_ddg.setCursor(Qt.CursorShape.PointingHandCursor)

        if current_engine == "DuckDuckGo":
            self.radio_ddg.setChecked(True)
        else:
            self.radio_google.setChecked(True)

        self.radio_google.toggled.connect(lambda checked: checked and self.set_search_engine("Google"))
        self.radio_ddg.toggled.connect(lambda checked: checked and self.set_search_engine("DuckDuckGo"))

        card_layout.addWidget(self.radio_google)
        card_layout.addWidget(self.radio_ddg)

        layout.addWidget(card)
        layout.addStretch()

        self.stack.addWidget(page)

    # --- Page 3: Appearance ---

    def _build_appearance_page(self):
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Appearance & Theme", page)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(title)

        subtitle = QLabel("Visual themes and glassmorphic customization", page)
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px; margin-bottom: 12px;")
        layout.addWidget(subtitle)

        card = QFrame(page)
        card.setProperty("class", "SettingsCard")
        card_layout = QVBoxLayout(card)

        theme_label = QLabel("Active Theme: Dark Glassmorphic (Default)", card)
        theme_label.setStyleSheet("color: #818cf8; font-weight: bold;")
        card_layout.addWidget(theme_label)

        desc = QLabel("Owl features an ultra-modern dark glass interface with smooth micro-animations and zero distractive elements.", card)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94a3b8; margin-top: 8px;")
        card_layout.addWidget(desc)

        layout.addWidget(card)
        layout.addStretch()
        self.stack.addWidget(page)

    # --- Page 4: About ---

    def _build_about_page(self):
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("About Owl", page)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(title)

        subtitle = QLabel("Next-Generation Private Workspace Browser", page)
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px; margin-bottom: 12px;")
        layout.addWidget(subtitle)

        card = QFrame(page)
        card.setProperty("class", "SettingsCard")
        card_layout = QVBoxLayout(card)

        ver = QLabel("Owl v2.0.0 (Stealth Build)", card)
        ver.setStyleSheet("font-weight: bold; font-size: 14px; color: #f8fafc;")
        card_layout.addWidget(ver)

        features = (
            "• Stealth Protection: SetWindowDisplayAffinity (WDA_EXCLUDEFROMCAPTURE)\n"
            "• Zero Disk Footprint: Ephemeral Off-The-Record QWebEngine Profile\n"
            "• Single-Instance Guard: Local Socket IPC Window Activation\n"
            "• Global Visibility Hotkey: Ctrl+Shift+B\n"
            "• Integrated AI Side Panel: ChatGPT Assistant"
        )
        features_label = QLabel(features, card)
        features_label.setStyleSheet("color: #cbd5e1; margin-top: 8px; line-height: 1.4;")
        card_layout.addWidget(features_label)

        layout.addWidget(card)
        layout.addStretch()
        self.stack.addWidget(page)

    # --- Public API Methods & Contracts ---

    def set_search_engine(self, engine: str):
        """Set active search engine ('Google' or 'DuckDuckGo') and emit signal."""
        valid_engine = engine if engine in VALID_SEARCH_ENGINES else "Google"

        if hasattr(self, "radio_google") and hasattr(self, "radio_ddg"):
            self.radio_google.blockSignals(True)
            self.radio_ddg.blockSignals(True)
            if valid_engine == "DuckDuckGo":
                self.radio_ddg.setChecked(True)
                self.radio_google.setChecked(False)
            else:
                self.radio_google.setChecked(True)
                self.radio_ddg.setChecked(False)
            self.radio_google.blockSignals(False)
            self.radio_ddg.blockSignals(False)

        if self.profile_manager:
            active = self.profile_manager.get_active_profile()
            if active:
                self.profile_manager.update_profile(active.id, search_engine=valid_engine)
                self._populate_active_profile_fields()
                self._sync_sub_pages()

        self.search_engine_changed.emit(valid_engine)

    def set_homepage(self, url: str):
        """Normalize homepage URL with https:// scheme, update active profile, and emit signal."""
        cleaned = url.strip() if url else ""
        if cleaned:
            schemes = ("http://", "https://", "file://", "chrome://", "phantom://", "owl://", "about:")
            if not cleaned.lower().startswith(schemes):
                cleaned = "https://" + cleaned
        else:
            cleaned = "https://www.google.com"

        if hasattr(self, "homepage_input"):
            self.homepage_input.blockSignals(True)
            self.homepage_input.setText(cleaned)
            self.homepage_input.blockSignals(False)

        if self.profile_manager:
            active = self.profile_manager.get_active_profile()
            if active:
                self.profile_manager.update_profile(active.id, homepage=cleaned)

        self.homepage_changed.emit(cleaned)
