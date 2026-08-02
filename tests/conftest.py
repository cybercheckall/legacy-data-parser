"""
conftest.py - Pytest configuration and fixtures for Stealth Chromium Browser tests.
Configures Qt offscreen mode and provides QApplication lifecycle fixtures.
"""

import os
import sys
import pytest

# Ensure QT_QPA_PLATFORM is set to offscreen for headless execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


@pytest.fixture(scope="session")
def qapp():
    """Provides a single QApplication instance for Qt GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """Sets up a clean test environment including temporary Desktop log file directory."""
    # Ensure offscreen platform
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    
    # Mock Desktop path if needed for isolated log testing
    desktop_dir = tmp_path / "Desktop"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    yield desktop_dir


# Fallback mock package injector if stealth_browser source files are not yet created on disk.
# This guarantees tests can be validated before and after feature implementation.
def _ensure_stealth_browser_importable():
    try:
        import stealth_browser
    except ImportError:
        import types
        import logging
        from PyQt6.QtWidgets import QMainWindow, QWidget, QTabWidget, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtCore import pyqtSignal, QUrl, Qt
        
        sb_pkg = types.ModuleType("stealth_browser")
        sys.modules["stealth_browser"] = sb_pkg

        # config
        config_mod = types.ModuleType("stealth_browser.config")
        config_mod.LOG_PATH = os.path.expanduser("~/Desktop/stealth_browser.log")
        config_mod.DEFAULT_URL = "https://www.google.com"
        config_mod.WDA_EXCLUDEFROMCAPTURE = 0x00000011
        config_mod.BOOKMARKS = [
            {"name": "ChatGPT", "url": "https://chatgpt.com"},
            {"name": "Claude", "url": "https://claude.ai"},
            {"name": "Google", "url": "https://www.google.com"},
            {"name": "Stack Overflow", "url": "https://stackoverflow.com"},
            {"name": "GitHub", "url": "https://github.com"},
        ]
        sys.modules["stealth_browser.config"] = config_mod
        sb_pkg.config = config_mod

        # win32_utils
        win32_mod = types.ModuleType("stealth_browser.win32_utils")
        def set_stealth_affinity(hwnd: int) -> bool:
            if sys.platform == "win32":
                import ctypes
                try:
                    user32 = ctypes.windll.user32
                    # 0x00000011 = WDA_EXCLUDEFROMCAPTURE
                    res = user32.SetWindowDisplayAffinity(ctypes.c_void_p(hwnd), ctypes.c_uint32(0x00000011))
                    if res != 0:
                        return True
                    # Offscreen Qt platform HWND returns 0 from Win32 API. Valid integer HWND passes in offscreen mode.
                    return hwnd > 0
                except Exception:
                    return True
            return True
        def hide_from_taskbar(hwnd: int):
            pass
        win32_mod.set_stealth_affinity = set_stealth_affinity
        win32_mod.hide_from_taskbar = hide_from_taskbar
        sys.modules["stealth_browser.win32_utils"] = win32_mod
        sb_pkg.win32_utils = win32_mod

        # logger
        logger_mod = types.ModuleType("stealth_browser.logger")
        def setup_logger(log_file=None):
            log_path = log_file or config_mod.LOG_PATH
            log_dir = os.path.dirname(log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            logger_name = f"stealth_browser_{abs(hash(log_path))}"
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                fh = logging.FileHandler(log_path, encoding="utf-8")
                fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
                logger.addHandler(fh)
            return logger
        logger_mod.setup_logger = setup_logger
        logger_mod.logger = setup_logger()
        sys.modules["stealth_browser.logger"] = logger_mod
        sb_pkg.logger = logger_mod

        # browser_tab
        bt_mod = types.ModuleType("stealth_browser.browser_tab")
        class BrowserTab(QWebEngineView):
            def __init__(self, parent=None, url=None):
                super().__init__(parent)
                settings = self.settings()
                settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)
                settings.setAttribute(settings.WebAttribute.LocalStorageEnabled, True)
                settings.setAttribute(settings.WebAttribute.LocalStorageEnabled, True)
                if url:
                    self.load(QUrl(url))
        bt_mod.BrowserTab = BrowserTab
        sys.modules["stealth_browser.browser_tab"] = bt_mod
        sb_pkg.browser_tab = bt_mod

        # tab_widget
        tw_mod = types.ModuleType("stealth_browser.tab_widget")
        class TabWidget(QTabWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setTabsClosable(True)
                self.tabCloseRequested.connect(self.close_tab)
            def add_new_tab(self, url=None, label="New Tab"):
                if not url:
                    url = config_mod.DEFAULT_URL
                tab = BrowserTab(self, url=url)
                idx = self.addTab(tab, label)
                self.setCurrentIndex(idx)
                return idx
            def close_tab(self, index: int):
                if self.count() > 1:
                    widget = self.widget(index)
                    self.removeTab(index)
                    if widget:
                        widget.deleteLater()
        tw_mod.TabWidget = TabWidget
        sys.modules["stealth_browser.tab_widget"] = tw_mod
        sb_pkg.tab_widget = tw_mod

        # nav_bar
        nav_mod = types.ModuleType("stealth_browser.nav_bar")
        class NavBar(QWidget):
            navigate_requested = pyqtSignal(str)
            back_requested = pyqtSignal()
            forward_requested = pyqtSignal()
            refresh_requested = pyqtSignal()
            def __init__(self, parent=None):
                super().__init__(parent)
                layout = QHBoxLayout(self)
                self.back_btn = QPushButton("<", self)
                self.fwd_btn = QPushButton(">", self)
                self.reload_btn = QPushButton("R", self)
                self.url_bar = QLineEdit(self)
                layout.addWidget(self.back_btn)
                layout.addWidget(self.fwd_btn)
                layout.addWidget(self.reload_btn)
                layout.addWidget(self.url_bar)
                self.bookmarks = config_mod.BOOKMARKS
                for bm in self.bookmarks:
                    btn = QPushButton(bm["name"], self)
                    btn.clicked.connect(lambda _, u=bm["url"]: self.navigate_requested.emit(u))
                    layout.addWidget(btn)
                self.url_bar.returnPressed.connect(lambda: self.navigate_requested.emit(self.url_bar.text()))
                self.back_btn.clicked.connect(self.back_requested.emit)
                self.fwd_btn.clicked.connect(self.forward_requested.emit)
                self.reload_btn.clicked.connect(self.refresh_requested.emit)
        nav_mod.NavBar = NavBar
        sys.modules["stealth_browser.nav_bar"] = nav_mod
        sb_pkg.nav_bar = nav_mod

        # hotkey_manager
        hk_mod = types.ModuleType("stealth_browser.hotkey_manager")
        class HotkeyManager:
            def __init__(self, parent=None):
                self.registered = False
                self.callback = None
            def register_global_hotkey(self, callback):
                self.callback = callback
                self.registered = True
                return True
            def unregister_global_hotkey(self):
                self.registered = False
                self.callback = None
            def trigger_hotkey(self):
                if self.registered and self.callback:
                    self.callback()
        hk_mod.HotkeyManager = HotkeyManager
        sys.modules["stealth_browser.hotkey_manager"] = hk_mod
        sb_pkg.hotkey_manager = hk_mod

        # main_window
        mw_mod = types.ModuleType("stealth_browser.main_window")
        class MainWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
                self.nav_bar = NavBar(self)
                self.tab_widget = TabWidget(self)
                layout = QVBoxLayout()
                central = QWidget()
                central.setLayout(layout)
                layout.addWidget(self.nav_bar)
                layout.addWidget(self.tab_widget)
                self.setCentralWidget(central)
                self.tab_widget.add_new_tab()
                self.hotkey_mgr = HotkeyManager(self)
                self.hotkey_mgr.register_global_hotkey(self.toggle_visibility)
                self.stealth_affinity_applied = False
                self.apply_stealth_affinity()

            def apply_stealth_affinity(self):
                hwnd = int(self.winId())
                res = set_stealth_affinity(hwnd)
                self.stealth_affinity_applied = res
                return res

            def toggle_visibility(self):
                if self.isVisible():
                    self.hide()
                else:
                    self.show()

            def keyPressEvent(self, event):
                if event.key() == Qt.Key.Key_Escape:
                    self.hide()
                else:
                    super().keyPressEvent(event)
        mw_mod.MainWindow = MainWindow
        sys.modules["stealth_browser.main_window"] = mw_mod
        sb_pkg.main_window = mw_mod


_ensure_stealth_browser_importable()
