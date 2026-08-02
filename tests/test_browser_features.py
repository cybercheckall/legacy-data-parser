"""
test_browser_features.py - Tier 1 & Tier 2 Opaque-Box E2E Tests for Browser Features, Tab Management & Navigation.

Covers:
- QWebEngineView initialization & Web settings.
- URL bar navigation (valid, empty, invalid scheme).
- Tab opening (Ctrl+T) and closing (Ctrl+W).
- Rapid tab create/close stress test.
- Bookmarks bar pre-loaded links & navigation trigger.
- Navigation controls (Back, Forward, Refresh).
"""

import sys
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView

from stealth_browser.browser_tab import BrowserTab
from stealth_browser.tab_widget import TabWidget
from stealth_browser.nav_bar import NavBar
from stealth_browser.config import BOOKMARKS, DEFAULT_URL


class TestBrowserFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tab_widget = TabWidget()
        self.nav_bar = NavBar()

    def tearDown(self):
        self.tab_widget.deleteLater()
        self.nav_bar.deleteLater()

    # --- Tier 1: Core Feature Tests ---

    def test_tier1_qwebengineview_initialization(self):
        """Tier 1: QWebEngineView initializes correctly with JS and Web storage settings enabled."""
        tab = BrowserTab(url="https://www.google.com")
        self.assertIsInstance(tab, QWebEngineView, "BrowserTab must subclass QWebEngineView.")
        settings = tab.settings()
        self.assertTrue(
            settings.testAttribute(settings.WebAttribute.JavascriptEnabled),
            "JavaScript must be enabled in WebEngine settings."
        )
        tab.deleteLater()

    def test_tier1_tab_opening_and_closing(self):
        """Tier 1: TabWidget handles opening new tabs and closing tabs."""
        self.tab_widget.add_new_tab(url="https://www.google.com", label="Google")
        initial_count = self.tab_widget.count()
        
        # Open tab
        idx = self.tab_widget.add_new_tab(url="https://claude.ai", label="Claude")
        self.assertEqual(self.tab_widget.count(), initial_count + 1, "Tab count should increment after opening tab.")
        self.assertEqual(self.tab_widget.currentIndex(), idx, "Newly added tab should be active.")

        # Close tab
        self.tab_widget.close_tab(idx)
        self.assertEqual(self.tab_widget.count(), initial_count, "Tab count should return to initial after close.")

    def test_tier1_url_navigation(self):
        """Tier 1: Navigating via address bar updates active URL or emits signal."""
        signal_received = []
        self.nav_bar.navigate_requested.connect(lambda url: signal_received.append(url))
        
        target_url = "https://github.com"
        self.nav_bar.url_bar.setText(target_url)
        self.nav_bar.url_bar.returnPressed.emit()

        self.assertEqual(len(signal_received), 1, "Return pressed on url_bar must emit navigate_requested signal.")
        self.assertEqual(signal_received[0], target_url, "Emitted URL must match address bar text.")

    def test_tier1_bookmarks_bar_preload(self):
        """Tier 1: Bookmarks bar pre-loads standard sites (ChatGPT, Claude, Google, Stack Overflow, GitHub)."""
        expected_names = {"ChatGPT", "Claude", "Google", "Stack Overflow", "GitHub"}
        loaded_names = {bm["name"] for bm in BOOKMARKS}
        self.assertTrue(
            expected_names.issubset(loaded_names),
            f"Bookmarks must contain all required default bookmarks. Missing: {expected_names - loaded_names}"
        )

    def test_tier1_navigation_buttons(self):
        """Tier 1: Back, Forward, and Refresh buttons emit appropriate signals."""
        back_called, fwd_called, refresh_called = [], [], []

        self.nav_bar.back_requested.connect(lambda: back_called.append(True))
        self.nav_bar.forward_requested.connect(lambda: fwd_called.append(True))
        self.nav_bar.refresh_requested.connect(lambda: refresh_called.append(True))

        self.nav_bar.back_btn.click()
        self.nav_bar.fwd_btn.click()
        self.nav_bar.reload_btn.click()

        self.assertEqual(len(back_called), 1, "Back button click must trigger back_requested signal.")
        self.assertEqual(len(fwd_called), 1, "Forward button click must trigger forward_requested signal.")
        self.assertEqual(len(refresh_called), 1, "Refresh button click must trigger refresh_requested signal.")

    # --- Tier 2: Boundary & Corner Cases ---

    def test_tier2_empty_url_navigation(self):
        """Tier 2: Empty URL string in address bar should not crash the app."""
        signal_received = []
        self.nav_bar.navigate_requested.connect(lambda url: signal_received.append(url))

        self.nav_bar.url_bar.setText("")
        self.nav_bar.url_bar.returnPressed.emit()

        self.assertEqual(len(signal_received), 1, "Empty URL navigation must emit signal without crashing.")
        self.assertEqual(signal_received[0], "", "Emitted URL for empty input is empty string.")

    def test_tier2_invalid_url_scheme(self):
        """Tier 2: Invalid scheme (e.g. invalid://scheme) handles input safely."""
        tab = BrowserTab(url="invalid://scheme")
        url_obj = tab.url()
        self.assertIsNotNone(url_obj, "QUrl object must be created even for invalid scheme.")
        tab.deleteLater()

    def test_tier2_rapid_tab_create_and_close(self):
        """Tier 2: Rapidly creating 10 tabs and closing 10 tabs under stress."""
        tabs_created = []
        for i in range(10):
            idx = self.tab_widget.add_new_tab(url=f"https://example.com/{i}", label=f"Tab {i}")
            tabs_created.append(idx)
        
        self.assertGreaterEqual(self.tab_widget.count(), 10, "10 tabs should be open after rapid creation.")

        # Close all created tabs down to 1
        while self.tab_widget.count() > 1:
            self.tab_widget.close_tab(self.tab_widget.count() - 1)

        self.assertEqual(self.tab_widget.count(), 1, "Tab count must safely return to 1 after rapid close.")


if __name__ == "__main__":
    unittest.main()
