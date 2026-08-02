"""
Phantom Browser — A full-featured stealth Chromium browser invisible to screen sharing.

Main application module with tabbed browsing, bookmarks, URL bar, and
SetWindowDisplayAffinity protection.
"""
import logging
import os
import sys

from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPushButton, QTabBar, QTabWidget, QToolBar, QVBoxLayout, QWidget,
    QSizePolicy, QStyle,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

from display_affinity import apply_display_affinity

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

HOME_URL = "https://www.google.com"


class WebTab(QWebEngineView):
    """A single browser tab backed by QWebEngineView."""

    def __init__(self, parent=None, profile=None):
        super().__init__(parent)
        if profile:
            page = QWebEnginePage(profile, self)
            self.setPage(page)

    def createWindow(self, window_type):
        """Handle requests to open a new window (e.g., target=_blank links)."""
        main_window = self.window()
        if isinstance(main_window, PhantomBrowser):
            return main_window.add_new_tab()
        return super().createWindow(window_type)


class PhantomBrowser(QMainWindow):
    """Main stealth browser window with tabbed browsing and bookmarks."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phantom Browser")

        # Window flags: frameless-ish but resizable, no taskbar icon, always on top
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # No taskbar icon
        )

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.resize(1100, 750)

        # Shared web engine profile for cookie/session persistence
        self._profile = QWebEngineProfile.defaultProfile()
        self._profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

        # --- Drag state ---
        self._drag_pos = None

        # --- Build UI ---
        self._build_ui()
        self._setup_shortcuts()

        # Apply display affinity after window is shown
        QTimer.singleShot(100, self._apply_stealth)

    def _build_ui(self):
        """Build the complete browser UI."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Custom title bar ---
        self._title_bar = QWidget()
        self._title_bar.setFixedHeight(30)
        self._title_bar.setStyleSheet(
            "background-color: #1a1a2e; color: #e0e0e0;"
        )
        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(8, 0, 4, 0)
        title_layout.setSpacing(4)

        title_label = QLabel("👻 Phantom Browser")
        title_label.setStyleSheet(
            "color: #a0a0d0; font-size: 12px; font-weight: bold; font-family: 'Segoe UI';"
        )
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # Minimize button
        min_btn = QPushButton("—")
        min_btn.setFixedSize(28, 22)
        min_btn.setStyleSheet(self._title_btn_style())
        min_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(min_btn)

        # Maximize/Restore button
        self._max_btn = QPushButton("□")
        self._max_btn.setFixedSize(28, 22)
        self._max_btn.setStyleSheet(self._title_btn_style())
        self._max_btn.clicked.connect(self._toggle_maximize)
        title_layout.addWidget(self._max_btn)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 22)
        close_btn.setStyleSheet(self._title_btn_style("#c0392b", "#e74c3c"))
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)

        layout.addWidget(self._title_bar)

        # --- Navigation toolbar ---
        nav_bar = QWidget()
        nav_bar.setFixedHeight(36)
        nav_bar.setStyleSheet("background-color: #16213e; padding: 2px;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(6, 2, 6, 2)
        nav_layout.setSpacing(4)

        btn_style = self._nav_btn_style()

        self._back_btn = QPushButton("◀")
        self._back_btn.setFixedSize(30, 28)
        self._back_btn.setStyleSheet(btn_style)
        self._back_btn.clicked.connect(self._go_back)
        nav_layout.addWidget(self._back_btn)

        self._fwd_btn = QPushButton("▶")
        self._fwd_btn.setFixedSize(30, 28)
        self._fwd_btn.setStyleSheet(btn_style)
        self._fwd_btn.clicked.connect(self._go_forward)
        nav_layout.addWidget(self._fwd_btn)

        self._refresh_btn = QPushButton("⟳")
        self._refresh_btn.setFixedSize(30, 28)
        self._refresh_btn.setStyleSheet(btn_style)
        self._refresh_btn.clicked.connect(self._refresh_page)
        nav_layout.addWidget(self._refresh_btn)

        self._url_bar = QLineEdit()
        self._url_bar.setPlaceholderText("Enter URL or search...")
        self._url_bar.setStyleSheet(
            """
            QLineEdit {
                background-color: #0f3460;
                color: #e0e0e0;
                border: 1px solid #1a1a4e;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
                font-family: 'Segoe UI';
                selection-background-color: #533483;
            }
            QLineEdit:focus {
                border: 1px solid #533483;
            }
            """
        )
        self._url_bar.returnPressed.connect(self._navigate_to_url)
        nav_layout.addWidget(self._url_bar)

        new_tab_btn = QPushButton("+")
        new_tab_btn.setFixedSize(30, 28)
        new_tab_btn.setStyleSheet(btn_style)
        new_tab_btn.setToolTip("New Tab (Ctrl+T)")
        new_tab_btn.clicked.connect(lambda: self.add_new_tab())
        nav_layout.addWidget(new_tab_btn)

        layout.addWidget(nav_bar)

        # --- Bookmarks bar ---
        bookmarks_bar = QWidget()
        bookmarks_bar.setFixedHeight(28)
        bookmarks_bar.setStyleSheet("background-color: #1a1a3e;")
        bm_layout = QHBoxLayout(bookmarks_bar)
        bm_layout.setContentsMargins(8, 0, 8, 0)
        bm_layout.setSpacing(4)

        for name, url in BOOKMARKS:
            btn = QPushButton(name)
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: transparent;
                    color: #8888cc;
                    border: none;
                    padding: 2px 8px;
                    font-size: 11px;
                    font-family: 'Segoe UI';
                }
                QPushButton:hover {
                    color: #bbbbff;
                    background-color: #2a2a5e;
                    border-radius: 3px;
                }
                """
            )
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, u=url: self._navigate(u))
            bm_layout.addWidget(btn)

        bm_layout.addStretch()
        layout.addWidget(bookmarks_bar)

        # --- Tab widget ---
        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.setMovable(True)
        self._tabs.setDocumentMode(True)
        self._tabs.tabCloseRequested.connect(self._close_tab)
        self._tabs.currentChanged.connect(self._on_tab_changed)
        self._tabs.setStyleSheet(
            """
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background-color: #1a1a3e;
                color: #8888aa;
                border: none;
                padding: 6px 14px;
                font-size: 12px;
                font-family: 'Segoe UI';
                min-width: 80px;
                max-width: 200px;
            }
            QTabBar::tab:selected {
                background-color: #16213e;
                color: #e0e0e0;
                border-bottom: 2px solid #533483;
            }
            QTabBar::tab:hover {
                background-color: #2a2a5e;
                color: #ccccee;
            }
            """
        )
        layout.addWidget(self._tabs)

        # Open the first tab
        self.add_new_tab(HOME_URL)

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Ctrl+T: New tab
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.add_new_tab())
        # Ctrl+W: Close current tab
        QShortcut(QKeySequence("Ctrl+W"), self, self._close_current_tab)
        # Ctrl+L: Focus URL bar
        QShortcut(QKeySequence("Ctrl+L"), self, self._focus_url_bar)
        # Ctrl+R / F5: Refresh
        QShortcut(QKeySequence("Ctrl+R"), self, self._refresh_page)
        QShortcut(QKeySequence("F5"), self, self._refresh_page)
        # Alt+Left: Back
        QShortcut(QKeySequence("Alt+Left"), self, self._go_back)
        # Alt+Right: Forward
        QShortcut(QKeySequence("Alt+Right"), self, self._go_forward)
        # Esc: Hide window
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

    def add_new_tab(self, url: str = None) -> WebTab:
        """Add a new browser tab and return the WebTab widget."""
        tab = WebTab(self, self._profile)
        idx = self._tabs.addTab(tab, "New Tab")
        self._tabs.setCurrentIndex(idx)

        tab.titleChanged.connect(
            lambda title, t=tab: self._update_tab_title(t, title)
        )
        tab.urlChanged.connect(
            lambda qurl, t=tab: self._update_url_bar(t, qurl)
        )

        if url:
            tab.setUrl(QUrl(url))
        else:
            tab.setUrl(QUrl(HOME_URL))

        logger.info("New tab opened: %s", url or HOME_URL)
        return tab

    def _close_tab(self, index: int):
        """Close tab at the given index."""
        if self._tabs.count() > 1:
            widget = self._tabs.widget(index)
            self._tabs.removeTab(index)
            widget.deleteLater()
        else:
            # Last tab — navigate to home instead of closing
            self._current_tab().setUrl(QUrl(HOME_URL))

    def _close_current_tab(self):
        """Close the currently active tab."""
        self._close_tab(self._tabs.currentIndex())

    def _current_tab(self) -> WebTab:
        """Get the currently active WebTab."""
        return self._tabs.currentWidget()

    def _on_tab_changed(self, index: int):
        """Update URL bar when switching tabs."""
        tab = self._tabs.widget(index)
        if tab and isinstance(tab, WebTab):
            self._url_bar.setText(tab.url().toString())

    def _update_tab_title(self, tab: WebTab, title: str):
        """Update tab title text."""
        idx = self._tabs.indexOf(tab)
        if idx >= 0:
            display_title = title[:25] + "..." if len(title) > 25 else title
            self._tabs.setTabText(idx, display_title or "New Tab")

    def _update_url_bar(self, tab: WebTab, qurl: QUrl):
        """Update URL bar when the current tab navigates."""
        if tab == self._current_tab():
            self._url_bar.setText(qurl.toString())

    # --- Navigation ---

    def _navigate_to_url(self):
        """Navigate to the URL typed in the URL bar."""
        text = self._url_bar.text().strip()
        if not text:
            return

        # If it looks like a URL, navigate directly
        if "." in text and " " not in text:
            if not text.startswith(("http://", "https://")):
                text = "https://" + text
            url = QUrl(text)
        else:
            # Otherwise, search with Google
            url = QUrl(f"https://www.google.com/search?q={text}")

        tab = self._current_tab()
        if tab:
            tab.setUrl(url)
            logger.info("Navigating to: %s", url.toString())

    def _navigate(self, url: str):
        """Navigate the current tab to a URL."""
        tab = self._current_tab()
        if tab:
            tab.setUrl(QUrl(url))

    def _go_back(self):
        tab = self._current_tab()
        if tab:
            tab.back()

    def _go_forward(self):
        tab = self._current_tab()
        if tab:
            tab.forward()

    def _refresh_page(self):
        tab = self._current_tab()
        if tab:
            tab.reload()

    def _focus_url_bar(self):
        self._url_bar.setFocus()
        self._url_bar.selectAll()

    # --- Window maximize toggle ---

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self._max_btn.setText("□")
        else:
            self.showMaximized()
            self._max_btn.setText("❐")

    # --- Title bar drag ---

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking on title bar area
            if self._title_bar.geometry().contains(event.pos()):
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if self._title_bar.geometry().contains(event.pos()):
            self._toggle_maximize()

    # --- Style helpers ---

    @staticmethod
    def _title_btn_style(bg_hover="#333366", bg_pressed="#444488"):
        return f"""
            QPushButton {{
                background-color: transparent;
                color: #a0a0c0;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {bg_hover};
                color: white;
            }}
            QPushButton:pressed {{
                background-color: {bg_pressed};
            }}
        """

    @staticmethod
    def _nav_btn_style():
        return """
            QPushButton {
                background-color: #0f3460;
                color: #a0a0d0;
                border: 1px solid #1a1a4e;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a4a7a;
                color: white;
            }
            QPushButton:pressed {
                background-color: #533483;
            }
        """
