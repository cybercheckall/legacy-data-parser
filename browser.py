"""
browser.py - Phantom Workspace Browser Main Window.

Assembles TitleBar, NavBar, TabWidget, BookmarksBar, and ProfileSelector into
the main PhantomBrowser window with dark glassmorphic styling and stealth affinity.
"""

import logging
import os
import sys

from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPushButton, QTabWidget, QVBoxLayout, QWidget, QStackedWidget,
    QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

from display_affinity import apply_display_affinity
from profile_manager import ProfileManager, Profile, create_otr_web_profile
from styles import DARK_GLASS_STYLE
from title_bar import TitleBar
from nav_bar import NavBar
from tab_bar import TabWidget
from profile_selector import ProfileSelector
from ai_panel import AIFloatingButton, AISidePanel
from settings_view import SettingsView

logger = logging.getLogger(__name__)

# --- Default bookmarks ---
BOOKMARKS = [
    ("ChatGPT", "https://chatgpt.com"),
    ("Claude", "https://claude.ai"),
    ("Google", "https://www.google.com"),
    ("Stack Overflow", "https://stackoverflow.com"),
    ("GitHub", "https://github.com"),
    ("LeetCode", "https://leetcode.com"),
]

HOME_URL = "file:///" + os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "home.html")).replace("\\", "/")


class WebTab(QWebEngineView):
    """A single browser tab backed by QWebEngineView."""

    def __init__(self, parent=None, profile=None):
        super().__init__(parent)
        if profile:
            page = QWebEnginePage(profile, self)
            self.setPage(page)

    def createWindow(self, window_type):
        """Handle requests to open a new window (e.g. target=_blank links)."""
        main_window = self.window()
        if isinstance(main_window, OwlBrowser):
            return main_window.add_new_tab()
        return super().createWindow(window_type)


class OwlBrowser(QMainWindow):
    """Main stealth browser window assembling all M2 modular UI components."""

    def __init__(self, show_profile_selector_on_start: bool = True):
        super().__init__()
        self.setWindowTitle("Owl")

        icon_path = os.path.join(os.path.dirname(__file__), "owl_icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(__file__), "owl_icon.jpg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Window flags: frameless-ish but resizable, no taskbar icon, always on top
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.resize(1100, 750)

        # Profile management & Off-The-Record QWebEngineProfile initialization
        self._profile_manager = ProfileManager()
        self._active_profile = self._profile_manager.get_active_profile()
        self._profile = create_otr_web_profile(self._active_profile, parent=self)

        # Apply central stylesheet
        self.setStyleSheet(DARK_GLASS_STYLE)

        # --- Build Stacked UI (Profile Selector vs Workspace) ---
        self._central_stack = QStackedWidget(self)
        self.setCentralWidget(self._central_stack)

        self._build_workspace_ui()
        self._build_profile_selector_ui()

        # Initialize AI Floating Sparkle Button & Side Panel
        self.ai_button = AIFloatingButton(self)
        self.ai_panel = AISidePanel(self)
        self.ai_button.clicked.connect(self.ai_panel.toggle_panel)
        self._reposition_ai_components()

        self._setup_shortcuts()

        if show_profile_selector_on_start:
            self.show_profile_selector()
        else:
            self.show_workspace()

        # Apply display affinity after window is shown
        QTimer.singleShot(100, self._apply_stealth)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_ai_components()

    def _reposition_ai_components(self):
        """Reposition floating AI button and update side panel geometry on resize."""
        bw = self.width()
        bh = self.height()
        is_selector_active = (
            hasattr(self, "_central_stack")
            and hasattr(self, "profile_selector")
            and self._central_stack.currentWidget() == self.profile_selector
        )

        if hasattr(self, "ai_button") and self.ai_button:
            btn_x = (bw - 52) // 2
            btn_y = bh - 52 - 24
            self.ai_button.move(btn_x, btn_y)
            if is_selector_active:
                self.ai_button.hide()
            else:
                self.ai_button.show()
                self.ai_button.raise_()

        if hasattr(self, "ai_panel") and self.ai_panel:
            pw = self.ai_panel.width()
            title_bar_h = 0
            if hasattr(self, "title_bar") and self.title_bar and self.title_bar.isVisible():
                title_bar_h = self.title_bar.height()
            
            panel_h = bh - title_bar_h
            is_expanded = getattr(self.ai_panel, "is_expanded", lambda: getattr(self.ai_panel, "_is_expanded", False))()
            if is_expanded:
                self.ai_panel.setGeometry(bw - pw, title_bar_h, pw, panel_h)
            else:
                self.ai_panel.setGeometry(bw, title_bar_h, pw, panel_h)
            self.ai_panel.raise_()

    def _build_workspace_ui(self):
        """Build main workspace view containing TitleBar, NavBar, BookmarksBar, and TabWidget."""
        self.workspace_widget = QWidget(self)
        ws_layout = QVBoxLayout(self.workspace_widget)
        ws_layout.setContentsMargins(0, 0, 0, 0)
        ws_layout.setSpacing(0)

        # Title Bar
        self.title_bar = TitleBar(self)
        self._title_bar = self.title_bar
        ws_layout.addWidget(self.title_bar)

        # Navigation Bar
        self.nav_bar = NavBar(self)
        self._nav_bar = self.nav_bar
        ws_layout.addWidget(self.nav_bar)

        # Hidden / Backwards compatibility button references
        self._back_btn = self.nav_bar.back_btn
        self._fwd_btn = self.nav_bar.fwd_btn
        self._refresh_btn = self.nav_bar.reload_btn
        self._url_bar = self.nav_bar.url_bar
        self.url_bar = self.nav_bar.url_bar

        # Connect NavBar signals
        self.nav_bar.navigate_requested.connect(self._navigate_from_input)
        self.nav_bar.refresh_requested.connect(self._refresh_page)
        self.nav_bar.settings_requested.connect(self._open_settings)
        self.nav_bar.profile_requested.connect(self.show_profile_selector)
        self.nav_bar.back_requested.connect(self._go_back)
        self.nav_bar.forward_requested.connect(self._go_forward)

        # Bookmarks Bar (instantiated but hidden/not added to layout to keep homepage clean per M4 R4)
        self.bookmarks_bar = QWidget(self)
        self.bookmarks_bar.setObjectName("BookmarksBar")
        self.bookmarks_bar.setFixedHeight(28)
        bm_layout = QHBoxLayout(self.bookmarks_bar)
        bm_layout.setContentsMargins(8, 0, 8, 0)
        bm_layout.setSpacing(4)

        for name, url in BOOKMARKS:
            btn = QPushButton(name, self.bookmarks_bar)
            btn.setProperty("class", "BookmarkBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, u=url: self._navigate(u))
            bm_layout.addWidget(btn)

        bm_layout.addStretch()
        self.bookmarks_bar.hide()

        # Tab Widget
        self.tab_widget = TabWidget(self, homepage_url=self._active_profile.homepage)
        self._tabs = self.tab_widget
        ws_layout.addWidget(self.tab_widget)

        self.tab_widget.new_tab_requested.connect(lambda: self.add_new_tab())
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        self._central_stack.addWidget(self.workspace_widget)

    def _build_profile_selector_ui(self):
        """Build ProfileSelector startup/overlay widget."""
        profiles = self._profile_manager.load_profiles()
        self.profile_selector = ProfileSelector(profiles=profiles, parent=self)
        self.profile_selector.profile_selected.connect(self._on_profile_selected)
        self._central_stack.addWidget(self.profile_selector)

    def show_workspace(self):
        """Switch central stack to main browser workspace."""
        self._central_stack.setCurrentWidget(self.workspace_widget)
        if hasattr(self, "ai_button") and self.ai_button:
            self.ai_button.show()
            self.ai_button.raise_()
        if self.tab_widget.count() == 0:
            self.add_new_tab(self._active_profile.homepage)

    def show_profile_selector(self):
        """Switch central stack to profile selector view."""
        profiles = self._profile_manager.load_profiles()
        self.profile_selector.set_profiles(profiles)
        self._central_stack.setCurrentWidget(self.profile_selector)
        if hasattr(self, "ai_button") and self.ai_button:
            self.ai_button.hide()
        if hasattr(self, "ai_panel") and self.ai_panel:
            self.ai_panel.hide_panel()

    def _on_profile_selected(self, profile: Profile):
        """Handle profile selection from profile selector screen."""
        logger.info("Switching to active profile: %s (%s)", profile.name, profile.id)
        self._profile_manager.set_active_profile(profile.id)
        self._active_profile = profile
        self._profile = create_otr_web_profile(profile, parent=self)
        self.tab_widget.set_homepage_url(profile.homepage)
        self.nav_bar.set_profile_avatar(profile.avatar)

        self.show_workspace()

    def activate_window_to_front(self):
        """Bring browser window to foreground and give focus."""
        if not self.isVisible():
            self.show()
        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()

    def _setup_shortcuts(self):
        """Set up global application keyboard shortcuts."""
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.add_new_tab())
        QShortcut(QKeySequence("Ctrl+W"), self, self._close_current_tab)
        QShortcut(QKeySequence("Ctrl+L"), self, self._focus_url_bar)
        QShortcut(QKeySequence("Ctrl+R"), self, self._refresh_page)
        QShortcut(QKeySequence("F5"), self, self._refresh_page)
        QShortcut(QKeySequence("Alt+Left"), self, self._go_back)
        QShortcut(QKeySequence("Alt+Right"), self, self._go_forward)
        QShortcut(QKeySequence("Escape"), self, self.hide)

    def _apply_stealth(self):
        """Apply display affinity to hide window from screen capture."""
        hwnd = int(self.winId())
        success = apply_display_affinity(hwnd)
        if success:
            logger.info("Stealth mode activated: window is invisible to screen capture.")
        else:
            logger.warning("Failed to activate stealth mode.")

    # --- Tab management ---

    def add_new_tab(self, url: str = None, label: str = "New Tab") -> WebTab:
        """Add a new browser tab using active profile's OTR profile and return WebTab widget."""
        tab = WebTab(self, self._profile)
        target_url = url if url else (self._active_profile.homepage if hasattr(self, "_active_profile") else HOME_URL)
        
        idx = self.tab_widget.addTab(tab, label)
        self.tab_widget.setCurrentIndex(idx)

        tab.titleChanged.connect(
            lambda title, t=tab: self._update_tab_title(t, title)
        )
        tab.urlChanged.connect(
            lambda qurl, t=tab: self._update_url_bar(t, qurl)
        )

        tab.setUrl(QUrl(target_url))
        logger.info("New tab opened: %s", target_url)
        return tab

    def close_tab(self, index: int):
        """Close tab at given index or navigate last tab home."""
        self.tab_widget.close_tab(index)

    def _close_tab(self, index: int):
        self.close_tab(index)

    def _close_current_tab(self):
        """Close currently active tab."""
        self.close_tab(self.tab_widget.currentIndex())

    def _current_tab(self) -> QWidget:
        """Get currently active tab widget."""
        return self.tab_widget.currentWidget()

    def _on_tab_changed(self, index: int):
        """Update URL bar when switching tabs."""
        tab = self.tab_widget.widget(index)
        if tab and hasattr(tab, "url"):
            self.nav_bar.set_url(tab.url().toString())

    def _update_tab_title(self, tab: QWidget, title: str):
        """Update tab title text with truncation."""
        idx = self.tab_widget.indexOf(tab)
        if idx >= 0:
            clean_title = title.strip() if (title and title.strip()) else "New Tab"
            display_title = clean_title[:25] + "..." if len(clean_title) > 25 else clean_title
            self.tab_widget.setTabText(idx, display_title)

    def _update_url_bar(self, tab: QWidget, qurl: QUrl):
        """Update URL bar when current tab navigates."""
        if tab == self._current_tab():
            self.nav_bar.set_url(qurl.toString())

    # --- Navigation & Query Parsing ---

    def _navigate_from_input(self, text: str):
        """Parse input text as direct URL, settings URL, or search query using active profile's search engine."""
        cleaned = text.strip()
        if not cleaned:
            return

        cleaned_lower = cleaned.lower()
        if cleaned_lower in ("chrome://settings", "phantom://settings", "owl://settings", "about:settings"):
            self._open_settings()
            return

        explicit_schemes = ("http://", "https://", "file://", "about:", "chrome://", "phantom://", "owl://", "ftp://", "data:")

        if cleaned_lower.startswith(explicit_schemes):
            url_str = cleaned
        elif (cleaned_lower.startswith("localhost") or cleaned_lower.startswith("127.0.0.1")) and " " not in cleaned:
            url_str = "http://" + cleaned
        elif "." in cleaned and " " not in cleaned:
            url_str = "https://" + cleaned
        else:
            if hasattr(self, "_active_profile") and hasattr(self._active_profile, "get_search_url"):
                url_str = self._active_profile.get_search_url(cleaned)
            else:
                import urllib.parse
                url_str = f"https://www.google.com/search?q={urllib.parse.quote_plus(cleaned)}"

        self._navigate(url_str)

    def _navigate(self, url: str):
        """Navigate current tab to specified URL string."""
        tab = self._current_tab()
        if tab and hasattr(tab, "setUrl"):
            tab.setUrl(QUrl(url))

    def _go_back(self):
        tab = self._current_tab()
        if tab and hasattr(tab, "back"):
            tab.back()

    def _go_forward(self):
        tab = self._current_tab()
        if tab and hasattr(tab, "forward"):
            tab.forward()

    def _refresh_page(self):
        tab = self._current_tab()
        if tab and hasattr(tab, "reload"):
            tab.reload()

    def _open_settings(self):
        """Open settings view in a dedicated deduplicated browser tab."""
        # Search for existing SettingsView tab
        for idx in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(idx)
            if isinstance(widget, SettingsView):
                self.tab_widget.setCurrentIndex(idx)
                self.nav_bar.set_url("owl://settings")
                return widget

        # Create new SettingsView tab
        settings_tab = SettingsView(profile_manager=self._profile_manager, parent=self)
        settings_tab.search_engine_changed.connect(self._on_search_engine_changed)
        settings_tab.homepage_changed.connect(self._on_homepage_changed)
        settings_tab.profile_updated.connect(self._on_profile_updated)

        tab_idx = self.tab_widget.addTab(settings_tab, "⚙ Settings")
        self.tab_widget.setCurrentIndex(tab_idx)
        self.nav_bar.set_url("owl://settings")
        logger.info("Opened SettingsView tab at index %d", tab_idx)
        return settings_tab

    def _on_search_engine_changed(self, engine: str):
        logger.info("Search engine updated to: %s", engine)
        self._active_profile = self._profile_manager.get_active_profile()

    def _on_homepage_changed(self, homepage: str):
        logger.info("Homepage updated to: %s", homepage)
        self._active_profile = self._profile_manager.get_active_profile()
        self.tab_widget.set_homepage_url(homepage)

    def _on_profile_updated(self):
        logger.info("Profile updated from Settings.")
        self._active_profile = self._profile_manager.get_active_profile()
        self.nav_bar.set_profile_avatar(self._active_profile.avatar)
        self.tab_widget.set_homepage_url(self._active_profile.homepage)

    def _focus_url_bar(self):
        self.nav_bar.url_bar.setFocus()
        self.nav_bar.url_bar.selectAll()

    # --- Window Controls ---

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.title_bar.max_btn.setText("□")
        else:
            self.showMaximized()
            self.title_bar.max_btn.setText("❐")

    def show_update_button(self, bat_script_path: str):
        """Show the OTA update restart button on the title bar."""
        if hasattr(self, "title_bar") and self.title_bar:
            import updater
            self.title_bar.show_update_button(bat_script_path, updater.apply_update)

PhantomBrowser = OwlBrowser
