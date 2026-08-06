"""
test_challenger_m3_stress.py - Comprehensive Adversarial Stress Tests for Milestone 3.

Adversarial stress-testing of:
1. Navigation routing (chrome://settings, phantom://settings, about:settings, scheme auto-prefixing, search queries via Google vs DuckDuckGo).
2. Concurrency and UI state synchronization (active profile, SettingsView, navbar avatar, search engine query generation, AI panel transitions).
"""

import sys
import os
import unittest
import tempfile
import urllib.parse
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QUrl

from browser import PhantomBrowser
from profile_manager import ProfileManager, Profile
from settings_view import SettingsView
from ai_panel import AISidePanel, AIFloatingButton


class TestNavigationRoutingAdversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "routing_profiles.json")
        # Ensure fresh profile manager for each test
        self.pm = ProfileManager(json_path=self.json_path)
        self.browser = PhantomBrowser(show_profile_selector_on_start=False)
        self.browser._profile_manager = self.pm
        self.browser._active_profile = self.pm.get_active_profile()

    def tearDown(self):
        self.browser.close()
        self.browser.deleteLater()
        self.tmp_dir.cleanup()

    def test_settings_url_routing_aliases(self):
        """Verify routing for chrome://settings, phantom://settings, about:settings with case & space variations."""
        aliases = [
            "chrome://settings",
            "phantom://settings",
            "about:settings",
            "CHROME://SETTINGS",
            "  phantom://settings  ",
            "About:Settings",
        ]

        for alias in aliases:
            # Clear tabs first
            while self.browser.tab_widget.count() > 0:
                self.browser.tab_widget.removeTab(0)
            self.browser.add_new_tab("https://www.google.com")

            self.browser._navigate_from_input(alias)

            # Check that a SettingsView tab was opened/activated
            current_widget = self.browser.tab_widget.currentWidget()
            self.assertIsInstance(current_widget, SettingsView, f"Failed for alias: '{alias}'")
            self.assertIn(self.browser.nav_bar.url_bar.text(), ("owl://settings", "phantom://settings"))

    def test_settings_tab_deduplication_stress(self):
        """Stress-test settings tab deduplication across 20 rapid invocations."""
        # Initial tab
        self.browser.add_new_tab("https://www.google.com")

        for i in range(20):
            alias = "chrome://settings" if i % 2 == 0 else "phantom://settings"
            self.browser._navigate_from_input(alias)

        # Verify only 1 SettingsView tab exists in total
        settings_count = 0
        for idx in range(self.browser.tab_widget.count()):
            if isinstance(self.browser.tab_widget.widget(idx), SettingsView):
                settings_count += 1

        self.assertEqual(settings_count, 1, "SettingsView tab must be deduplicated to exactly 1 tab.")
        self.assertIsInstance(self.browser.tab_widget.currentWidget(), SettingsView)

    def test_url_vs_search_query_parsing_matrix(self):
        """Test url vs search query classification matrix."""
        # Set active profile engine to Google
        self.browser._active_profile.search_engine = "Google"
        self.browser.nav_bar.navigate_requested.connect(self.browser._navigate_from_input)

        test_cases = [
            # (Input, Expected URL prefix or exact string)
            ("https://github.com", "https://github.com"),
            ("http://localhost:8080", "http://localhost:8080"),
            ("localhost:3000", "http://localhost:3000"),
            ("127.0.0.1:5000/api", "http://127.0.0.1:5000/api"),
            ("file:///C:/index.html", "file:///C:/index.html"),
            ("data:text/html,<h1>Hello</h1>", QUrl("data:text/html,<h1>Hello</h1>").toString()),
            ("example.com", "https://example.com"),
            ("sub.domain.co.uk/path", "https://sub.domain.co.uk/path"),
        ]

        for inp, expected_url in test_cases:
            self.browser._navigate_from_input(inp)
            current_tab = self.browser._current_tab()
            self.assertEqual(current_tab.url().toString(), expected_url, f"Failed parsing for: '{inp}'")

    def test_search_query_url_generation_google_vs_duckduckgo(self):
        """Verify search query URL generation for Google vs DuckDuckGo engines."""
        query = "pyqt6 browser & stealth 100%"
        encoded_q = urllib.parse.quote_plus(query)

        # 1. Google
        self.browser._active_profile.search_engine = "Google"
        self.browser._navigate_from_input(query)
        tab_url = self.browser._current_tab().url().toString()
        expected_google = f"https://www.google.com/search?q={encoded_q}"
        self.assertEqual(tab_url, expected_google)

        # 2. DuckDuckGo
        self.browser._active_profile.search_engine = "DuckDuckGo"
        self.browser._navigate_from_input(query)
        tab_url = self.browser._current_tab().url().toString()
        expected_ddg = f"https://duckduckgo.com/?q={encoded_q}"
        self.assertEqual(tab_url, expected_ddg)


class TestConcurrencyAndUIStateSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "sync_profiles.json")
        self.pm = ProfileManager(json_path=self.json_path)
        self.browser = PhantomBrowser(show_profile_selector_on_start=False)
        self.browser._profile_manager = self.pm
        self.browser._active_profile = self.pm.get_active_profile()
        self.browser.show()

    def tearDown(self):
        self.browser.close()
        self.browser.deleteLater()
        self.tmp_dir.cleanup()

    def profile_switch_search_engine_sync(self):
        pass

    def test_profile_switch_search_engine_sync(self):
        """Verify active profile selection dynamically updates search query URL generation."""
        profiles = self.pm.load_profiles()
        p1 = profiles[0]
        p2 = profiles[1] if len(profiles) > 1 else self.pm.create_profile(name="Work Profile", search_engine="DuckDuckGo")

        self.pm.update_profile(p1.id, search_engine="Google")
        self.pm.update_profile(p2.id, search_engine="DuckDuckGo")

        # Select Profile 1
        self.browser._on_profile_selected(p1)
        self.browser._navigate_from_input("quantum physics")
        self.assertIn("google.com", self.browser._current_tab().url().toString())

        # Select Profile 2
        self.browser._on_profile_selected(p2)
        self.browser._navigate_from_input("quantum physics")
        self.assertIn("duckduckgo.com", self.browser._current_tab().url().toString())

    def test_settings_view_and_profile_manager_bidirectional_sync(self):
        """Verify SettingsView updates active profile, emitting signals and updating navbar avatar."""
        settings_view = self.browser._open_settings()

        # Switch search engine via SettingsView
        settings_view.set_search_engine("DuckDuckGo")
        active = self.pm.get_active_profile()
        self.assertEqual(active.search_engine, "DuckDuckGo")

        # Update homepage via SettingsView
        settings_view.set_homepage("https://news.ycombinator.com")
        active = self.pm.get_active_profile()
        self.assertEqual(active.homepage, "https://news.ycombinator.com")
        self.assertEqual(self.browser.tab_widget._homepage_url, "https://news.ycombinator.com")

        # Update profile avatar via SettingsView save
        settings_view.prof_avatar_input.setText("🚀")
        settings_view._on_save_active_profile()
        self.assertEqual(self.browser.nav_bar.profile_btn.text(), "🚀")

    def test_rapid_profile_crud_while_settings_open(self):
        """Stress-test profile CRUD operations with open SettingsView and ensure active profile stability."""
        settings_view = self.browser._open_settings()

        # Rapidly create 5 profiles
        created_ids = []
        for i in range(5):
            p = self.pm.create_profile(f"Stress Profile {i}", avatar="⚡", search_engine="DuckDuckGo")
            self.assertIsNotNone(p)
            created_ids.append(p.id)

        settings_view._refresh_profile_combo()
        self.assertGreaterEqual(settings_view.prof_select_combo.count(), 6)

        # Delete 4 of the created profiles
        for pid in created_ids[:4]:
            self.pm.delete_profile(pid)

        settings_view._refresh_profile_combo()
        active = self.pm.get_active_profile()
        self.assertIsNotNone(active, "Active profile must remain non-None after deletions.")

        # Ensure active profile cannot be deleted when it's the last one remaining
        remaining = self.pm.load_profiles()
        for p in remaining[1:]:
            self.pm.delete_profile(p.id)

        self.assertFalse(self.pm.delete_profile(remaining[0].id), "Deleting sole remaining profile must fail.")
        self.assertEqual(len(self.pm.load_profiles()), 1)

    def test_ai_panel_concurrency_and_geometry_sync(self):
        """Test rapid AI side panel toggling concurrent with window resizing and tab creation."""
        ai_panel = self.browser.ai_panel
        ai_button = self.browser.ai_button

        self.assertIsNotNone(ai_panel)
        self.assertIsNotNone(ai_button)

        for i in range(10):
            if i % 2 == 0:
                ai_panel.show_panel()
                self.assertTrue(ai_panel.is_expanded())
                self.assertTrue(ai_panel._is_expanded)
            else:
                ai_panel.hide_panel()
                self.assertFalse(ai_panel.is_expanded())
                self.assertFalse(ai_panel._is_expanded)

            # Trigger resize during toggle
            self.browser.resize(1000 + i * 20, 700 + i * 10)
            self.browser._reposition_ai_components()

            # Add tab during toggle
            self.browser.add_new_tab("https://www.google.com")

        # Final check
        ai_panel.hide_panel()
        self.assertFalse(ai_panel.is_expanded())

    def test_multitab_settings_interaction(self):
        """Verify settings changes propagate search engine updates across multiple tabs immediately."""
        # Create 5 tabs
        for i in range(5):
            self.browser.add_new_tab("https://www.google.com", label=f"Tab {i}")

        # Open settings
        settings_view = self.browser._open_settings()
        settings_view.set_search_engine("DuckDuckGo")

        # Switch to Tab 2 and search
        self.browser.tab_widget.setCurrentIndex(2)
        self.browser._navigate_from_input("stealth test query")
        self.assertIn("duckduckgo.com", self.browser._current_tab().url().toString())

        # Switch back to settings tab, switch to Google
        settings_idx = self.browser.tab_widget.indexOf(settings_view)
        self.browser.tab_widget.setCurrentIndex(settings_idx)
        settings_view.set_search_engine("Google")

        # Switch to Tab 4 and search
        self.browser.tab_widget.setCurrentIndex(4)
        self.browser._navigate_from_input("stealth test query")
        self.assertIn("google.com", self.browser._current_tab().url().toString())


if __name__ == "__main__":
    unittest.main()
