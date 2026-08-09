"""
test_profiles.py - Tier 1 & Tier 2 Opaque-Box E2E Tests for Profiles Manager & Schema.

Covers:
- Profile model schema & JSON file persistence.
- Profile CRUD (Create, Read, Update, Delete) operations.
- Active profile switching & default generation.
- Ephemeral off-the-record (OTR) QWebEngineProfile creation (zero persistent cookies/cache).
- Boundary conditions: corrupt JSON fallback, active profile deletion, last profile protection, search engine validation, unicode/emoji handling.
"""

import sys
import os
import json
import unittest
import tempfile
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile

from owl.profiles.profile_manager import Profile, ProfileManager, create_otr_web_profile


class TestProfilesManagerAndSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "profiles.json")
        self.manager = ProfileManager(json_path=self.json_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    # --- Tier 1: Happy-Path Test Cases (≥5) ---

    def test_tier1_default_profile_creation(self):
        """Tier 1: ProfileManager creates default profiles when initialized with no pre-existing file."""
        profiles = self.manager.load_profiles()
        self.assertEqual(len(profiles), 1, "ProfileManager must initialize with 1 Guest mode profile by default.")
        self.assertEqual(profiles[0].name, "Guest mode", "Default profile name must be Guest mode.")
        self.assertEqual(profiles[0].id, "guest", "Default profile id must be guest.")
        active = self.manager.get_active_profile()
        self.assertIsNotNone(active, "An active profile must be selected by default.")
        self.assertEqual(active.name, "Guest mode", "Active profile name must be Guest mode.")
        self.assertTrue(os.path.exists(self.json_path), "JSON profile file must be created on disk.")

    def test_tier1_profile_persistence(self):
        """Tier 1: Creating a profile persists to JSON file and reloads in a new ProfileManager instance."""
        new_prof = self.manager.create_profile(
            name="Developer Workspace",
            avatar="💻",
            homepage="https://github.com",
            search_engine="DuckDuckGo"
        )
        self.assertEqual(new_prof.name, "Developer Workspace")

        # Reload from disk using fresh ProfileManager
        new_manager = ProfileManager(json_path=self.json_path)
        reloaded_profiles = new_manager.load_profiles()
        reloaded_names = [p.name for p in reloaded_profiles]
        self.assertIn("Developer Workspace", reloaded_names, "Newly created profile must persist to JSON file.")

    def test_tier1_active_profile_switch(self):
        """Tier 1: Switching active profile updates current state and persists across reloads."""
        new_prof = self.manager.create_profile(name="Research", avatar="🔬")
        success = self.manager.set_active_profile(new_prof.id)
        self.assertTrue(success, "set_active_profile must return True for valid profile ID.")

        active = self.manager.get_active_profile()
        self.assertEqual(active.id, new_prof.id, "Active profile ID must match switched profile ID.")

        # Reload and check persistence of active profile ID
        reloaded_manager = ProfileManager(json_path=self.json_path)
        self.assertEqual(reloaded_manager.get_active_profile().id, new_prof.id)

    def test_tier1_profile_crud_operations(self):
        """Tier 1: Full CRUD (Create, Read, Update, Delete) workflow for profiles."""
        # Create
        prof = self.manager.create_profile(name="Temp Profile", homepage="https://example.com")
        pid = prof.id

        # Update
        updated = self.manager.update_profile(pid, name="Updated Profile", search_engine="DuckDuckGo")
        self.assertEqual(updated.name, "Updated Profile")
        self.assertEqual(updated.search_engine, "DuckDuckGo")

        # Read
        active = self.manager.get_active_profile()
        self.assertIsNotNone(active)

        # Delete
        del_success = self.manager.delete_profile(pid)
        self.assertTrue(del_success, "Deleting non-last profile must return True.")

    def test_tier1_otr_web_profile_creation(self):
        """Tier 1: create_otr_web_profile creates off-the-record QWebEngineProfile with zero cookie persistence."""
        prof = self.manager.get_active_profile()
        web_profile = create_otr_web_profile(prof)
        self.assertIsInstance(web_profile, QWebEngineProfile)
        self.assertEqual(
            web_profile.persistentCookiesPolicy(),
            QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies,
            "Private profile must enforce NoPersistentCookies."
        )

    # --- Tier 2: Boundary & Corner Cases (≥5) ---

    def test_tier2_corrupt_json_fallback(self):
        """Tier 2: Corrupt/malformed JSON file cleanly falls back to default profile schema."""
        with open(self.json_path, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON CORRUPT $$$ }")

        reloaded_manager = ProfileManager(json_path=self.json_path)
        profiles = reloaded_manager.load_profiles()
        self.assertGreaterEqual(len(profiles), 1, "Corrupt JSON must gracefully fall back to default profiles.")
        self.assertIsNotNone(reloaded_manager.get_active_profile())

    def test_tier2_delete_active_profile(self):
        """Tier 2: Deleting the currently active profile automatically reassigns active profile to remaining."""
        prof1 = self.manager.create_profile(name="Prof 1")
        prof2 = self.manager.create_profile(name="Prof 2")
        self.manager.set_active_profile(prof1.id)

        # Delete active prof1
        self.manager.delete_profile(prof1.id)
        current_active = self.manager.get_active_profile()
        self.assertNotEqual(current_active.id, prof1.id, "Active profile must switch when current active profile is deleted.")

    def test_tier2_delete_last_profile_prevention(self):
        """Tier 2: Attempting to delete the last remaining profile is prevented (returns False)."""
        # Delete profiles down to 1
        profiles = list(self.manager.profiles)
        for p in profiles[1:]:
            self.manager.delete_profile(p.id)

        self.assertEqual(len(self.manager.profiles), 1)
        last_id = self.manager.profiles[0].id
        res = self.manager.delete_profile(last_id)
        self.assertFalse(res, "Deleting the last remaining profile must be prevented.")
        self.assertEqual(len(self.manager.profiles), 1, "Profile count must remain 1.")

    def test_tier2_invalid_search_engine_validation(self):
        """Tier 2: Setting invalid search engine (not Google/DuckDuckGo) defaults safely to Google."""
        prof = self.manager.create_profile(name="Search Test", search_engine="YahooInvalid")
        self.assertEqual(prof.search_engine, "Google", "Invalid search engine must default to Google.")

        updated = self.manager.update_profile(prof.id, search_engine="BaiduInvalid")
        self.assertEqual(updated.search_engine, "Google", "Updating to invalid search engine must default to Google.")

    def test_tier2_special_char_profile_names(self):
        """Tier 2: Profile names with Unicode, emojis, and special characters persist without error."""
        special_name = "🚀 Quantum & Privacy 🔒 — (Testing: <script>alert(1)</script>)"
        prof = self.manager.create_profile(name=special_name, avatar="🛡️")
        self.assertEqual(prof.name, special_name)

        new_manager = ProfileManager(json_path=self.json_path)
        reloaded = [p for p in new_manager.load_profiles() if p.id == prof.id][0]
        self.assertEqual(reloaded.name, special_name, "Unicode and special characters must persist intact.")


if __name__ == "__main__":
    unittest.main()
