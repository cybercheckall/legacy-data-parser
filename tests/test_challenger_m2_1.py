"""
test_challenger_m2_1.py - Challenger M2-1 Adversarial & Stress Test Suite for Milestone 2.

Empirically tests:
1. Rapid tab creation/deletion, churn, index bounds, and last-tab fallback.
2. TitleBar drag offset calculations, maximize immunity, and button interactions.
3. ProfileSelector handling of empty, None, or corrupted profile lists, and set_profiles() layout/widget lifecycle.
4. Navigation URL bar input parsing for domain URLs, search queries, local hosts, file schemes, and empty inputs.
"""

import sys
import unittest
from PyQt6.QtCore import Qt, QPoint, QPointF, QUrl, QEvent
from PyQt6.QtGui import QMouseEvent, QAction
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView

from owl.shell.title_bar import TitleBar
from owl.shell.nav_bar import NavBar
from owl.shell.tab_bar import TabWidget
from owl.profiles.profile_selector import ProfileSelector
from owl.profiles.profile_manager import Profile, ProfileManager
from owl.workspace.main_window import PhantomBrowser


class TestRapidTabChurnAndStress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tab_widget = TabWidget(homepage_url="https://www.google.com")

    def tearDown(self):
        self.tab_widget.deleteLater()

    def test_rapid_tab_creation_and_deletion(self):
        """Stress test creating 50 tabs rapidly and closing them in various sequences."""
        # 1. Create 50 tabs
        for i in range(50):
            idx = self.tab_widget.add_new_tab(url="https://example.com", label=f"Tab {i}")
            self.assertEqual(self.tab_widget.count(), i + 1)
            self.assertEqual(self.tab_widget.currentIndex(), i)

        self.assertEqual(self.tab_widget.count(), 50)

        # 2. Close middle tabs until 10 remain
        while self.tab_widget.count() > 10:
            mid = self.tab_widget.count() // 2
            self.tab_widget.close_tab(mid)

        self.assertEqual(self.tab_widget.count(), 10)

        # 3. Close from index 0 until 1 tab remains
        while self.tab_widget.count() > 1:
            self.tab_widget.close_tab(0)

        self.assertEqual(self.tab_widget.count(), 1)

        # 4. Closing the final tab should NOT remove it, but navigate to homepage
        self.tab_widget.close_tab(0)
        self.assertEqual(self.tab_widget.count(), 1)
        self.assertEqual(self.tab_widget.tabText(0), "Home")

    def test_close_tab_invalid_index(self):
        """Verify close_tab with out-of-bounds indices does not crash."""
        self.tab_widget.add_new_tab("https://example.com", "Tab 1")
        self.tab_widget.add_new_tab("https://example.org", "Tab 2")
        initial_count = self.tab_widget.count()

        # Negative index when count > 1
        self.tab_widget.close_tab(-1)
        # Large index when count > 1
        self.tab_widget.close_tab(999)

        # Count should remain intact or safely handled without uncaught exceptions
        self.assertTrue(self.tab_widget.count() >= 1)

    def test_tab_title_truncation_and_whitespace(self):
        """Verify dynamic title update with long titles, whitespace, and empty strings."""
        view = QWebEngineView()
        self.tab_widget.addTab(view, "Initial")

        # Test long title truncation (> 25 chars)
        long_title = "This is a very long web page title that exceeds 25 characters"
        self.tab_widget._update_tab_title(view, long_title)
        display_title = self.tab_widget.tabText(0)
        self.assertTrue(display_title.endswith("..."))
        self.assertEqual(len(display_title), 28)  # 25 + 3 dots

        # Test whitespace title
        self.tab_widget._update_tab_title(view, "   ")
        self.assertEqual(self.tab_widget.tabText(0), "New Tab")

        # Test None title
        self.tab_widget._update_tab_title(view, None)
        self.assertEqual(self.tab_widget.tabText(0), "New Tab")


class TestTitleBarDragAndControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.win = QMainWindow()
        self.win.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.win.resize(800, 600)
        self.win.move(100, 100)
        self.title_bar = TitleBar(self.win)
        self.win.setMenuWidget(self.title_bar)
        self.win.show()

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()

    def test_drag_offset_calculation(self):
        """Test drag event offset calculation moves window accurately."""
        initial_pos = self.win.pos()

        # Simulate left mouse press at global (150, 110)
        press_point = QPoint(150, 110)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(50.0, 10.0),
            press_point.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.title_bar.mousePressEvent(press_event)

        # Expected drag offset = press_point - initial_pos
        expected_offset = press_point - initial_pos
        self.assertEqual(self.title_bar._drag_pos, expected_offset)

        # Simulate mouse move to (250, 210)
        move_point = QPoint(250, 210)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(150.0, 110.0),
            move_point.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.title_bar.mouseMoveEvent(move_event)

        # Expected new window position = move_point - expected_offset = (200, 200)
        expected_new_pos = move_point - expected_offset
        self.assertEqual(self.win.pos(), expected_new_pos)

        # Simulate mouse release
        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            QPointF(150.0, 110.0),
            move_point.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.title_bar.mouseReleaseEvent(release_event)
        self.assertIsNone(self.title_bar._drag_pos)

    def test_maximized_window_drag_immunity(self):
        """Verify window dragging is suppressed when window is maximized."""
        self.win.showMaximized()
        self.assertTrue(self.win.isMaximized())

        press_point = QPoint(150, 110)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(50.0, 10.0),
            press_point.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.title_bar.mousePressEvent(press_event)
        # Drag pos must be None when maximized
        self.assertIsNone(self.title_bar._drag_pos)

    def test_double_click_toggle_maximize(self):
        """Test double-clicking title bar toggles maximize state."""
        self.win.showNormal()
        self.assertFalse(self.win.isMaximized())

        dbl_click_event = QMouseEvent(
            QEvent.Type.MouseButtonDblClick,
            QPointF(50.0, 10.0),
            QPoint(150, 110).toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.title_bar.mouseDoubleClickEvent(dbl_click_event)
        self.assertTrue(self.win.isMaximized())
        self.assertEqual(self.title_bar.max_btn.text(), "❐")

        # Double click again to restore
        self.title_bar.mouseDoubleClickEvent(dbl_click_event)
        self.assertFalse(self.win.isMaximized())
        self.assertEqual(self.title_bar.max_btn.text(), "□")


class TestProfileSelectorEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_empty_and_none_profiles_list(self):
        """Test ProfileSelector instantiation with empty and None profile lists."""
        ps1 = ProfileSelector(profiles=[])
        self.assertEqual(len(ps1.cards), 0)
        ps1.deleteLater()

        ps2 = ProfileSelector(profiles=None)
        self.assertEqual(len(ps2.cards), 0)
        ps2.deleteLater()

    def test_set_profiles_multiple_calls_widget_lifecycle(self):
        """Test calling set_profiles() multiple times to inspect card regeneration."""
        p1 = Profile(id="p1", name="Profile 1", avatar="👤", homepage="https://google.com", search_engine="Google", theme_color="#6366f1")
        p2 = Profile(id="p2", name="Profile 2", avatar="🦊", homepage="https://duckduckgo.com", search_engine="DuckDuckGo", theme_color="#10b981")

        ps = ProfileSelector(profiles=[p1])
        self.assertEqual(len(ps.cards), 1)

        # Update profiles to 2 items
        ps.set_profiles([p1, p2])
        self.assertEqual(len(ps.cards), 2)

        # Update profiles back to empty
        ps.set_profiles([])
        self.assertEqual(len(ps.cards), 0)

        ps.deleteLater()

    def test_card_click_signal_emission(self):
        """Test clicking a profile card emits profile_selected signal with correct Profile payload."""
        p1 = Profile(id="test_id", name="Test Profile", avatar="🔒", homepage="https://example.com", search_engine="Google", theme_color="#000000")
        ps = ProfileSelector(profiles=[p1])

        emitted_profiles = []
        ps.profile_selected.connect(lambda prof: emitted_profiles.append(prof))

        # Click the card button
        self.assertEqual(len(ps.cards), 1)
        ps.cards[0].click()

        self.assertEqual(len(emitted_profiles), 1)
        self.assertEqual(emitted_profiles[0].id, "test_id")
        ps.deleteLater()


class TestNavigationUrlParsing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.browser = PhantomBrowser(show_profile_selector_on_start=False)

    def tearDown(self):
        self.browser.close()
        self.browser.deleteLater()

    def test_url_input_parsing_domain(self):
        """Test parsing domain names into https:// URLs."""
        navigated_urls = []
        self.browser._navigate = lambda url: navigated_urls.append(url)

        self.browser._navigate_from_input("google.com")
        self.assertEqual(navigated_urls[-1], "https://google.com")

        self.browser._navigate_from_input("subdomain.example.org/path?q=1")
        self.assertEqual(navigated_urls[-1], "https://subdomain.example.org/path?q=1")

    def test_url_input_parsing_explicit_scheme(self):
        """Test parsing inputs with explicit http:// or https:// schemes."""
        navigated_urls = []
        self.browser._navigate = lambda url: navigated_urls.append(url)

        self.browser._navigate_from_input("http://example.com")
        self.assertEqual(navigated_urls[-1], "http://example.com")

        self.browser._navigate_from_input("https://secure.site.com")
        self.assertEqual(navigated_urls[-1], "https://secure.site.com")

    def test_url_input_parsing_search_queries(self):
        """Test parsing plain text queries into search engine URLs."""
        navigated_urls = []
        self.browser._navigate = lambda url: navigated_urls.append(url)

        self.browser._navigate_from_input("pyqt6 tutorial 2026")
        self.assertTrue("search?q=pyqt6" in navigated_urls[-1])

        # Search query containing dot and space
        self.browser._navigate_from_input("python 3.12 release notes")
        self.assertTrue("search?q=python" in navigated_urls[-1])

    def test_url_input_parsing_empty_and_spaces(self):
        """Test parsing empty string or whitespace-only inputs does not navigate."""
        navigated_urls = []
        self.browser._navigate = lambda url: navigated_urls.append(url)

        self.browser._navigate_from_input("")
        self.assertEqual(len(navigated_urls), 0)

        self.browser._navigate_from_input("   ")
        self.assertEqual(len(navigated_urls), 0)

    def test_url_input_parsing_localhost_and_files(self):
        """Test parsing localhost:port, 127.0.0.1, file://, and about: URIs."""
        navigated_urls = []
        self.browser._navigate = lambda url: navigated_urls.append(url)

        self.browser._navigate_from_input("localhost:8080")
        self.assertEqual(navigated_urls[-1], "http://localhost:8080")

        self.browser._navigate_from_input("127.0.0.1:3000")
        self.assertEqual(navigated_urls[-1], "http://127.0.0.1:3000")

        self.browser._navigate_from_input("file:///C:/path/page.html")
        self.assertEqual(navigated_urls[-1], "file:///C:/path/page.html")

        self.browser._navigate_from_input("about:blank")
        self.assertEqual(navigated_urls[-1], "about:blank")


if __name__ == "__main__":
    unittest.main()
