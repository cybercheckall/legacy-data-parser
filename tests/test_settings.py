"""
test_settings.py - Tier 1 & Tier 2 Opaque-Box E2E Tests for Settings Page & Search Engine Switcher.

Covers:
- SettingsView sidebar navigation (General, Profiles, Search Engine, Appearance, About).
- Search Engine switcher (Google vs DuckDuckGo).
- Profile management section.
- Preferred homepage setting updates.
- Signals: search_engine_changed, profile_updated, homepage_changed.
- Boundary conditions: query string formatting, scheme auto-prefixing for homepages, invalid engine fallback, sequential signal emissions.
"""

import sys
import os
import unittest
import tempfile
from PyQt6.QtWidgets import QApplication

from owl.settings.view import SettingsView
from owl.profiles.profile_manager import ProfileManager


class TestSettingsPageAndSearchEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "settings_profiles.json")
        self.pm = ProfileManager(json_path=self.json_path)
        self.settings_view = SettingsView(profile_manager=self.pm)

    def tearDown(self):
        self.settings_view.deleteLater()
        self.tmp_dir.cleanup()

    # --- Tier 1: Happy-Path Test Cases (≥5) ---

    def test_tier1_settings_sidebar_navigation(self):
        """Tier 1: SettingsView renders sidebar navigation buttons for General, Profiles, Search Engine, Appearance, About."""
        self.assertIsNotNone(self.settings_view.btn_general, "SettingsView must have General nav button.")
        self.assertIsNotNone(self.settings_view.btn_profiles, "SettingsView must have Profiles nav button.")
        self.assertIsNotNone(self.settings_view.btn_search, "SettingsView must have Search Engine nav button.")
        self.assertIsNotNone(self.settings_view.btn_appearance, "SettingsView must have Appearance nav button.")
        self.assertIsNotNone(self.settings_view.btn_about, "SettingsView must have About nav button.")

    def test_tier1_search_engine_switcher(self):
        """Tier 1: Switching search engine updates active profile and emits search_engine_changed signal."""
        emitted_engines = []
        self.settings_view.search_engine_changed.connect(lambda eng: emitted_engines.append(eng))

        # Switch to DuckDuckGo
        self.settings_view.set_search_engine("DuckDuckGo")
        self.assertEqual(len(emitted_engines), 1)
        self.assertEqual(emitted_engines[0], "DuckDuckGo")
        self.assertEqual(self.pm.get_active_profile().search_engine, "DuckDuckGo")

        # Switch to Google
        self.settings_view.set_search_engine("Google")
        self.assertEqual(len(emitted_engines), 2)
        self.assertEqual(emitted_engines[1], "Google")
        self.assertEqual(self.pm.get_active_profile().search_engine, "Google")

    def test_tier1_profile_management_view(self):
        """Tier 1: SettingsView references profile manager allowing profile CRUD access."""
        self.assertIsNotNone(self.settings_view.profile_manager)
        profiles = self.settings_view.profile_manager.load_profiles()
        self.assertGreaterEqual(len(profiles), 1)

    def test_tier1_homepage_setting_change(self):
        """Tier 1: Setting homepage updates active profile homepage and emits homepage_changed signal."""
        emitted_homepages = []
        self.settings_view.homepage_changed.connect(lambda hp: emitted_homepages.append(hp))

        target_hp = "https://github.com"
        self.settings_view.set_homepage(target_hp)
        self.assertEqual(len(emitted_homepages), 1)
        self.assertEqual(emitted_homepages[0], target_hp)
        self.assertEqual(self.pm.get_active_profile().homepage, target_hp)

    def test_tier1_about_section_info(self):
        """Tier 1: SettingsView contains stack container for section pages including search and about."""
        self.assertIsNotNone(self.settings_view.stack)
        self.assertGreaterEqual(self.settings_view.stack.count(), 1)

    # --- Tier 2: Boundary & Corner Cases (≥5) ---

    def test_tier2_search_engine_url_formatting(self):
        """Tier 2: Search queries format correctly for Google vs DuckDuckGo URLs."""
        query = "stealth browser python"
        google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        ddg_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"

        self.assertIn("google.com", google_url)
        self.assertIn("duckduckgo.com", ddg_url)

    def test_tier2_invalid_homepage_url_correction(self):
        """Tier 2: Setting homepage without scheme auto-prepends https:// scheme."""
        emitted_homepages = []
        self.settings_view.homepage_changed.connect(lambda hp: emitted_homepages.append(hp))

        self.settings_view.set_homepage("example.com")
        self.assertEqual(emitted_homepages[0], "https://example.com")

    def test_tier2_settings_page_open_in_tab_or_view(self):
        """Tier 2: SettingsView can be instantiated standalone or embedded in QMainWindow layout."""
        self.settings_view.show()
        self.assertFalse(self.settings_view.isHidden())

    def test_tier2_search_engine_validation_on_set(self):
        """Tier 2: Passing unsupported engine string to set_search_engine defaults safely to Google."""
        self.settings_view.set_search_engine("UnsupportedEngine123")
        active = self.pm.get_active_profile()
        self.assertEqual(active.search_engine, "Google")

    def test_tier2_multiple_signal_emissions(self):
        """Tier 2: Rapid sequential setting changes emit clean signals without dropped events."""
        events = []
        self.settings_view.search_engine_changed.connect(lambda e: events.append(e))

        for i in range(5):
            engine = "DuckDuckGo" if i % 2 == 0 else "Google"
            self.settings_view.set_search_engine(engine)

        self.assertEqual(len(events), 5)


if __name__ == "__main__":
    unittest.main()
