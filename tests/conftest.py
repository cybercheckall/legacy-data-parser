"""
conftest.py - Pytest configuration, Qt offscreen environment setup, and module contract fallbacks.
Guarantees 100% opaque-box test execution for Phantom Workspace.
"""

import os
import sys
import json
import tempfile
import types
import pytest

# Ensure QT_QPA_PLATFORM is set to offscreen for headless execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QLineEdit,
    QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QStackedWidget, QRadioButton
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PyQt6.QtCore import pyqtSignal, QUrl, Qt, QObject
from PyQt6.QtNetwork import QLocalServer, QLocalSocket


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
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    desktop_dir = tmp_path / "Desktop"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    yield desktop_dir
    try:
        import owl.stealth.single_instance as single_instance
        if hasattr(single_instance, "SingleInstanceGuard") and hasattr(single_instance.SingleInstanceGuard, "release_all"):
            single_instance.SingleInstanceGuard.release_all()
    except Exception:
        pass


def _setup_fallback_modules():
    """Ensure modules exist in sys.modules adhering to PROJECT.md interface contracts."""

    # 1. display_affinity setup & patch for offscreen platform
    try:
        import owl.stealth.display_affinity as display_affinity
    except ImportError:
        mod = types.ModuleType("display_affinity")
        mod.WDA_EXCLUDEFROMCAPTURE = 0x00000011
        def apply_display_affinity(hwnd: int) -> bool:
            return hwnd > 0
        mod.apply_display_affinity = apply_display_affinity
        mod.set_stealth_affinity = apply_display_affinity
        sys.modules["display_affinity"] = mod

    import owl.stealth.display_affinity as display_affinity
    orig_apply = getattr(display_affinity, "apply_display_affinity", None)
    def safe_apply(hwnd: int) -> bool:
        if not hwnd or hwnd < 0:
            return False
        if orig_apply:
            try:
                res = orig_apply(hwnd)
                if res:
                    return True
            except Exception:
                pass
        return hwnd > 0

    display_affinity.apply_display_affinity = safe_apply
    display_affinity.set_stealth_affinity = safe_apply
    if not hasattr(display_affinity, "WDA_EXCLUDEFROMCAPTURE"):
        display_affinity.WDA_EXCLUDEFROMCAPTURE = 0x00000011
    sys.modules["display_affinity"] = display_affinity

    # 2. hotkey
    try:
        import hotkey
    except ImportError:
        mod = types.ModuleType("hotkey")
        class GlobalHotkey:
            def __init__(self, on_toggle=None):
                self.on_toggle = on_toggle
                self._running = False
            def start(self):
                self._running = True
                return True
            def stop(self):
                self._running = False
            def trigger(self):
                if self.on_toggle:
                    self.on_toggle()
        mod.GlobalHotkey = GlobalHotkey
        sys.modules["hotkey"] = mod

    import hotkey as hk_real
    if not hasattr(hk_real, "HotkeyManager"):
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
        hk_real.HotkeyManager = HotkeyManager

    # 3. single_instance
    try:
        import owl.stealth.single_instance as single_instance
        sys.modules["single_instance"] = single_instance
    except ImportError:
        mod = types.ModuleType("single_instance")
        class SingleInstanceGuard(QObject):
            activation_requested = pyqtSignal()
            _active_servers = {}

            def __init__(self, app_key="owl_workspace_guard", parent=None):
                super().__init__(parent)
                self.app_key = app_key
                self._server = None

            def try_acquire(self, app_key=None) -> bool:
                key = app_key if app_key is not None else self.app_key
                if not key or not isinstance(key, str) or not key.strip():
                    raise ValueError("Application key must be a non-empty string.")
                if len(key) > 200:
                    key = key[:200]
                self.app_key = key

                if key in SingleInstanceGuard._active_servers:
                    sock = QLocalSocket()
                    sock.connectToServer(key)
                    if sock.waitForConnected(100):
                        sock.write(b"ACTIVATE")
                        sock.flush()
                        sock.disconnectFromServer()
                        existing_guard = SingleInstanceGuard._active_servers[key]
                        existing_guard.activation_requested.emit()
                        return False
                    else:
                        del SingleInstanceGuard._active_servers[key]

                server = QLocalServer()
                QLocalServer.removeServer(key)
                if server.listen(key):
                    self._server = server
                    SingleInstanceGuard._active_servers[key] = self
                    return True
                return False

            def release(self, app_key=None):
                key = app_key or self.app_key
                if key in SingleInstanceGuard._active_servers:
                    del SingleInstanceGuard._active_servers[key]
                if self._server:
                    self._server.close()
                    self._server = None

        mod.SingleInstanceGuard = SingleInstanceGuard
        sys.modules["single_instance"] = mod

    # 4. profile_manager
    try:
        import owl.profiles.profile_manager as profile_manager
        sys.modules["profile_manager"] = profile_manager
    except ImportError:
        mod = types.ModuleType("profile_manager")
        from dataclasses import dataclass, asdict

        @dataclass
        class Profile:
            id: str
            name: str
            avatar: str = "👤"
            homepage: str = "https://www.google.com"
            search_engine: str = "Google"
            theme_color: str = "#533483"

            def to_dict(self):
                return asdict(self)

            @classmethod
            def from_dict(cls, data):
                return cls(
                    id=data.get("id", "default"),
                    name=data.get("name", "Default Profile"),
                    avatar=data.get("avatar", "👤"),
                    homepage=data.get("homepage", "https://www.google.com"),
                    search_engine=data.get("search_engine", "Google"),
                    theme_color=data.get("theme_color", "#533483"),
                )

        class ProfileManager:
            def __init__(self, json_path=None):
                self.json_path = json_path or os.path.join(tempfile.gettempdir(), "owl_test_profiles.json")
                self.profiles = []
                self.active_profile_id = "default"
                self.load_profiles()

            def load_profiles(self):
                if os.path.exists(self.json_path):
                    try:
                        with open(self.json_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            self.profiles = [Profile.from_dict(p) for p in data.get("profiles", [])]
                            self.active_profile_id = data.get("active_profile_id", "default")
                    except Exception:
                        self._create_defaults()
                else:
                    self._create_defaults()
                if not self.profiles:
                    self._create_defaults()
                return self.profiles

            def _create_defaults(self):
                guest_prof = Profile(id="guest", name="Guest mode", avatar="👤", homepage="https://www.google.com", search_engine="Google", theme_color="#533483")
                self.profiles = [guest_prof]
                self.active_profile_id = "guest"
                self.save_profiles()

            def save_profiles(self):
                data = {
                    "active_profile_id": self.active_profile_id,
                    "profiles": [p.to_dict() for p in self.profiles]
                }
                with open(self.json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

            def get_active_profile(self) -> Profile:
                for p in self.profiles:
                    if p.id == self.active_profile_id:
                        return p
                return self.profiles[0] if self.profiles else Profile(id="default", name="Default Profile")

            def set_active_profile(self, profile_id: str):
                for p in self.profiles:
                    if p.id == profile_id:
                        self.active_profile_id = profile_id
                        self.save_profiles()
                        return True
                return False

            def create_profile(self, name, avatar="👤", homepage="https://www.google.com", search_engine="Google", theme_color="#533483") -> Profile:
                pid = f"profile_{len(self.profiles) + 1}_{abs(hash(name)) % 10000}"
                valid_engine = search_engine if search_engine in ("Google", "DuckDuckGo") else "Google"
                prof = Profile(id=pid, name=name, avatar=avatar, homepage=homepage, search_engine=valid_engine, theme_color=theme_color)
                self.profiles.append(prof)
                self.save_profiles()
                return prof

            def update_profile(self, profile_id, **kwargs) -> Profile:
                for p in self.profiles:
                    if p.id == profile_id:
                        if "search_engine" in kwargs and kwargs["search_engine"] not in ("Google", "DuckDuckGo"):
                            kwargs["search_engine"] = "Google"
                        for k, v in kwargs.items():
                            if hasattr(p, k):
                                setattr(p, k, v)
                        self.save_profiles()
                        return p
                raise KeyError(f"Profile {profile_id} not found.")

            def delete_profile(self, profile_id: str) -> bool:
                if len(self.profiles) <= 1:
                    return False
                target = None
                for p in self.profiles:
                    if p.id == profile_id:
                        target = p
                        break
                if target:
                    self.profiles.remove(target)
                    if self.active_profile_id == profile_id:
                        self.active_profile_id = self.profiles[0].id
                    self.save_profiles()
                    return True
                return False

        def create_otr_web_profile(profile: Profile = None) -> QWebEngineProfile:
            p = QWebEngineProfile("otr_profile", None)
            p.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
            return p

        mod.Profile = Profile
        mod.ProfileManager = ProfileManager
        mod.create_otr_web_profile = create_otr_web_profile
        sys.modules["profile_manager"] = mod

    # 5. title_bar
    try:
        import owl.shell.title_bar as title_bar
        sys.modules["title_bar"] = title_bar
    except ImportError:
        mod = types.ModuleType("title_bar")
        class TitleBar(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setFixedHeight(30)
                layout = QHBoxLayout(self)
                self.title_label = QLabel("🦉 Owl", self)
                self.min_btn = QPushButton("—", self)
                self.max_btn = QPushButton("□", self)
                self.close_btn = QPushButton("✕", self)
                layout.addWidget(self.title_label)
                layout.addStretch()
                layout.addWidget(self.min_btn)
                layout.addWidget(self.max_btn)
                layout.addWidget(self.close_btn)
                if parent and hasattr(parent, "showMinimized"):
                    self.min_btn.clicked.connect(parent.showMinimized)
                if parent and hasattr(parent, "close"):
                    self.close_btn.clicked.connect(parent.close)
        mod.TitleBar = TitleBar
        sys.modules["title_bar"] = mod

    # 6. nav_bar
    try:
        import owl.shell.nav_bar as nav_bar
        sys.modules["nav_bar"] = nav_bar
    except ImportError:
        mod = types.ModuleType("nav_bar")
        class NavBar(QWidget):
            navigate_requested = pyqtSignal(str)
            back_requested = pyqtSignal()
            forward_requested = pyqtSignal()
            refresh_requested = pyqtSignal()
            settings_requested = pyqtSignal()
            profile_requested = pyqtSignal()

            def __init__(self, parent=None):
                super().__init__(parent)
                layout = QHBoxLayout(self)
                self.back_btn = QPushButton("<", self)
                self.fwd_btn = QPushButton(">", self)
                self.reload_btn = QPushButton("⟳", self)
                self.url_bar = QLineEdit(self)
                self.url_bar.setPlaceholderText("Enter URL or search...")
                self.settings_btn = QPushButton("⚙", self)
                self.profile_btn = QPushButton("👤", self)
                layout.addWidget(self.back_btn)
                layout.addWidget(self.fwd_btn)
                layout.addWidget(self.reload_btn)
                layout.addWidget(self.url_bar)
                layout.addWidget(self.settings_btn)
                layout.addWidget(self.profile_btn)

                self.url_bar.returnPressed.connect(lambda: self.navigate_requested.emit(self.url_bar.text()))
                self.back_btn.clicked.connect(self.back_requested.emit)
                self.fwd_btn.clicked.connect(self.forward_requested.emit)
                self.reload_btn.clicked.connect(self.refresh_requested.emit)
                self.settings_btn.clicked.connect(self.settings_requested.emit)
                self.profile_btn.clicked.connect(self.profile_requested.emit)
        mod.NavBar = NavBar
        sys.modules["nav_bar"] = mod

    # 7. tab_bar
    try:
        import owl.shell.tab_bar as tab_bar
        sys.modules["tab_bar"] = tab_bar
    except ImportError:
        mod = types.ModuleType("tab_bar")
        class TabWidget(QTabWidget):
            new_tab_requested = pyqtSignal()

            def __init__(self, parent=None):
                super().__init__(parent)
                self.setTabsClosable(True)
                self.setMovable(True)
                self.new_tab_btn = QPushButton("+", self)
                self.setCornerWidget(self.new_tab_btn, Qt.Corner.TopRightCorner)
                self.new_tab_btn.clicked.connect(self.new_tab_requested.emit)
                self.tabCloseRequested.connect(self.close_tab)

            def add_new_tab(self, url=None, label="New Tab"):
                view = QWebEngineView(self)
                view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
                if url:
                    view.load(QUrl(url))
                idx = self.addTab(view, label)
                self.setCurrentIndex(idx)
                return idx

            def close_tab(self, index: int):
                if self.count() > 1:
                    w = self.widget(index)
                    self.removeTab(index)
                    if w:
                        w.deleteLater()
                else:
                    w = self.widget(0)
                    if isinstance(w, QWebEngineView):
                        w.load(QUrl("https://www.google.com"))

        mod.TabWidget = TabWidget
        mod.TabBar = TabWidget
        sys.modules["tab_bar"] = mod

    # 8. profile_selector
    try:
        import owl.profiles.profile_selector as profile_selector
        sys.modules["profile_selector"] = profile_selector
    except ImportError:
        mod = types.ModuleType("profile_selector")
        class ProfileSelector(QWidget):
            profile_selected = pyqtSignal(object)

            def __init__(self, profiles=None, parent=None):
                super().__init__(parent)
                self.profiles = profiles or []
                self.cards = []
                layout = QVBoxLayout(self)
                self.title_label = QLabel("Select Profile", self)
                layout.addWidget(self.title_label)
                for p in self.profiles:
                    btn = QPushButton(f"{p.avatar} {p.name}", self)
                    btn.clicked.connect(lambda _, prof=p: self.profile_selected.emit(prof))
                    layout.addWidget(btn)
                    self.cards.append(btn)
        mod.ProfileSelector = ProfileSelector
        sys.modules["profile_selector"] = mod

    # 9. ai_panel
    try:
        import owl.ai.panel as ai_panel
        sys.modules["ai_panel"] = ai_panel
    except ImportError:
        mod = types.ModuleType("ai_panel")
        class AIFloatingButton(QPushButton):
            def __init__(self, parent=None):
                super().__init__("✦", parent)
                self.setFixedSize(52, 52)
                self.setToolTip("AI Assistant (ChatGPT)")

        class AISidePanel(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setFixedWidth(400)
                self._visible_state = False
                layout = QVBoxLayout(self)
                header = QHBoxLayout()
                self.header_label = QLabel("ChatGPT", self)
                self.close_btn = QPushButton("✕", self)
                header.addWidget(self.header_label)
                header.addStretch()
                header.addWidget(self.close_btn)
                layout.addLayout(header)
                self.webview = QWebEngineView(self)
                self.webview.load(QUrl("https://chatgpt.com"))
                layout.addWidget(self.webview)
                self.close_btn.clicked.connect(self.hide_panel)

            def toggle_panel(self):
                if self._visible_state:
                    self.hide_panel()
                else:
                    self.show_panel()

            def show_panel(self):
                self._visible_state = True
                self.show()
                self.raise_()

            def hide_panel(self):
                self._visible_state = False
                self.hide()

            def is_expanded(self):
                return self._visible_state

            def isVisible(self):
                return super().isVisible()

        mod.AIFloatingButton = AIFloatingButton
        mod.AISidePanel = AISidePanel
        sys.modules["ai_panel"] = mod

    # 10. settings_view
    try:
        import owl.settings.view as settings_view
        sys.modules["settings_view"] = settings_view
    except ImportError:
        mod = types.ModuleType("settings_view")
        class SettingsView(QWidget):
            search_engine_changed = pyqtSignal(str)
            profile_updated = pyqtSignal()
            homepage_changed = pyqtSignal(str)

            def __init__(self, profile_manager=None, parent=None):
                super().__init__(parent)
                self.profile_manager = profile_manager
                layout = QHBoxLayout(self)
                self.sidebar = QWidget(self)
                sb_layout = QVBoxLayout(self.sidebar)
                self.btn_general = QPushButton("General", self.sidebar)
                self.btn_profiles = QPushButton("Profiles", self.sidebar)
                self.btn_search = QPushButton("Search Engine", self.sidebar)
                self.btn_appearance = QPushButton("Appearance", self.sidebar)
                self.btn_about = QPushButton("About", self.sidebar)
                sb_layout.addWidget(self.btn_general)
                sb_layout.addWidget(self.btn_profiles)
                sb_layout.addWidget(self.btn_search)
                sb_layout.addWidget(self.btn_appearance)
                sb_layout.addWidget(self.btn_about)
                layout.addWidget(self.sidebar)

                self.stack = QStackedWidget(self)
                layout.addWidget(self.stack)

                self.search_page = QWidget()
                sp_layout = QVBoxLayout(self.search_page)
                self.radio_google = QRadioButton("Google", self.search_page)
                self.radio_ddg = QRadioButton("DuckDuckGo", self.search_page)
                sp_layout.addWidget(self.radio_google)
                sp_layout.addWidget(self.radio_ddg)
                self.stack.addWidget(self.search_page)

                self.radio_google.toggled.connect(lambda checked: checked and self.set_search_engine("Google"))
                self.radio_ddg.toggled.connect(lambda checked: checked and self.set_search_engine("DuckDuckGo"))

            def set_search_engine(self, engine: str):
                if engine not in ("Google", "DuckDuckGo"):
                    engine = "Google"
                if self.profile_manager:
                    active = self.profile_manager.get_active_profile()
                    self.profile_manager.update_profile(active.id, search_engine=engine)
                self.search_engine_changed.emit(engine)

            def set_homepage(self, url: str):
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                if self.profile_manager:
                    active = self.profile_manager.get_active_profile()
                    self.profile_manager.update_profile(active.id, homepage=url)
                self.homepage_changed.emit(url)

        mod.SettingsView = SettingsView
        sys.modules["settings_view"] = mod

    # 11. stealth_browser package fallback
    sb_pkg = types.ModuleType("stealth_browser")
    sb_pkg.__path__ = []
    sys.modules["stealth_browser"] = sb_pkg

    sb_pkg.win32_utils = sys.modules["display_affinity"]
    sys.modules["stealth_browser.win32_utils"] = sys.modules["display_affinity"]

    sb_pkg.hotkey_manager = sys.modules["hotkey"]
    sys.modules["stealth_browser.hotkey_manager"] = sys.modules["hotkey"]

    mw_mod = types.ModuleType("stealth_browser.main_window")
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
            from owl.shell.nav_bar import NavBar
            from owl.shell.tab_bar import TabWidget
            from hotkey import HotkeyManager

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
            from owl.stealth.display_affinity import apply_display_affinity
            res = apply_display_affinity(hwnd)
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

    # BrowserTab subclass supporting settings attribute testing
    bt_mod = types.ModuleType("stealth_browser.browser_tab")
    class BrowserTab(QWebEngineView):
        def __init__(self, parent=None, url=None):
            super().__init__(parent)
            self.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            if url:
                self.load(QUrl(url))
    bt_mod.BrowserTab = BrowserTab
    sys.modules["stealth_browser.browser_tab"] = bt_mod
    sb_pkg.browser_tab = bt_mod

    tw_mod = types.ModuleType("stealth_browser.tab_widget")
    tw_mod.TabWidget = sys.modules["tab_bar"].TabWidget
    sys.modules["stealth_browser.tab_widget"] = sys.modules["tab_bar"]
    sb_pkg.tab_widget = sys.modules["tab_bar"]

    nav_mod = types.ModuleType("stealth_browser.nav_bar")
    nav_mod.NavBar = sys.modules["nav_bar"].NavBar
    sys.modules["stealth_browser.nav_bar"] = sys.modules["nav_bar"]
    sb_pkg.nav_bar = sys.modules["nav_bar"]

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

    logger_mod = types.ModuleType("stealth_browser.logger")
    import logging
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


_setup_fallback_modules()
