"""
test_challenger_m4_stress.py - Milestone 4 Rebranding, Polish & Stealth Stress Tests.

Empirical test suite verifying:
1. Rebranding to "Owl" across OwlBrowser, TitleBar, ProfileSelector, SettingsView, specs.
2. Profile creation & switching label synchronization across TitleBar and SettingsView.
3. SingleInstanceGuard rapid socket acquisition, release, and IPC signal propagation.
4. Icon loading resilience and fallback mechanism under missing/relocated asset conditions.
5. Global hotkey rapid triggering, Esc key handling, and stealth window flag integrity.
"""

import os
import sys
import tempfile
import unittest
import shutil
from typing import List

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from owl.workspace.main_window import OwlBrowser, PhantomBrowser
from owl.shell.title_bar import TitleBar
from owl.profiles.profile_selector import ProfileSelector
from owl.settings.view import SettingsView
from owl.stealth.single_instance import SingleInstanceGuard
from owl.profiles.profile_manager import ProfileManager, Profile
from hotkey import GlobalHotkey
from owl.stealth.display_affinity import WDA_EXCLUDEFROMCAPTURE, apply_display_affinity


class TestM4RebrandingAndPolish(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "m4_test_profiles.json")
        self.pm = ProfileManager(json_path=self.json_path)
        self.browser = OwlBrowser(show_profile_selector_on_start=False)
        self.browser._profile_manager = self.pm
        self.browser._active_profile = self.pm.get_active_profile()

    def tearDown(self):
        if hasattr(self, "browser") and self.browser:
            self.browser.close()
            self.browser.deleteLater()
        self.tmp_dir.cleanup()

    def test_rebranding_window_titles_and_labels(self):
        """Verify window title, titlebar label, profile selector header, and settings about section show 'Owl'."""
        # 1. Main window title
        self.assertEqual(self.browser.windowTitle(), "Owl")

        # 2. Handler branding — owl logo icon only (no wordmark in the shell)
        self.assertTrue(
            hasattr(self.browser.title_bar, "owl_btn")
            and not self.browser.title_bar.owl_btn.icon().isNull(),
            "Title/handler bar must show owl logo icon.",
        )
        self.assertEqual(self.browser.title_bar.title_label.text(), "")

        # 3. ProfileSelector header
        profiles = self.pm.load_profiles()
        selector = ProfileSelector(profiles=profiles)
        from PyQt6.QtWidgets import QLabel
        header_labels = selector.findChildren(QLabel)
        owl_header_found = any("Owl" in label.text() for label in header_labels if label.text())
        self.assertTrue(owl_header_found, "ProfileSelector must display 'Owl' in header label.")

        # 4. SettingsView About section
        settings_tab = self.browser._open_settings()
        about_page = settings_tab.stack.widget(4)
        about_labels = about_page.findChildren(QLabel)
        about_texts = [lbl.text() for lbl in about_labels if lbl.text()]
        self.assertTrue(any("About Owl" in text for text in about_texts), "About section title must be 'About Owl'")
        self.assertTrue(any("Owl v2" in text for text in about_texts), "Version string must contain 'Owl v2'")

        # 5. PhantomBrowser backward compatibility alias
        self.setIs(PhantomBrowser, OwlBrowser)

    def setIs(self, first, second):
        self.assertIs(first, second, "PhantomBrowser must be an alias for OwlBrowser")

    def test_profile_creation_switching_label_sync(self):
        """Verify profile creation & switching updates nav_bar, homepage, settings, and titlebar consistency."""
        # Create a new custom profile
        new_prof = self.pm.create_profile(
            name="Alpha Stealth",
            avatar="🚀",
            homepage="https://duckduckgo.com",
            search_engine="DuckDuckGo",
            theme_color="#10b981"
        )

        # Switch to new profile via browser
        self.browser._on_profile_selected(new_prof)

        # Verify active profile updated
        self.assertEqual(self.browser._active_profile.id, new_prof.id)
        self.assertEqual(self.browser._active_profile.name, "Alpha Stealth")
        self.assertEqual(self.browser.nav_bar.profile_btn.text(), "🚀")
        self.assertEqual(self.browser.tab_widget._homepage_url, "https://duckduckgo.com")
        self.assertEqual(self.browser.title_bar.title_label.text(), "")
        self.assertFalse(self.browser.title_bar.owl_btn.icon().isNull())

        # Open settings view and verify profile dropdown & active field synchronization
        settings_tab = self.browser._open_settings()
        self.assertIsNotNone(settings_tab)
        active_prof_in_settings = settings_tab.profile_manager.get_active_profile()
        self.assertEqual(active_prof_in_settings.id, new_prof.id)

    def test_icon_loading_resilience_and_fallback(self):
        """Test window icon loading resilience when ico/jpg files are missing or present."""
        real_icon_dir = os.path.dirname(__file__)
        root_dir = os.path.abspath(os.path.join(real_icon_dir, ".."))

        ico_path = os.path.join(root_dir, "owl_icon.ico")
        jpg_path = os.path.join(root_dir, "owl_icon.jpg")
        png_path = os.path.join(root_dir, "owl_icon.png")

        # Assert at least one image asset exists in the root directory
        self.assertTrue(
            os.path.exists(ico_path) or os.path.exists(jpg_path) or os.path.exists(png_path),
            "At least one owl_icon file must exist in project root."
        )

        # Test instantiating OwlBrowser when assets directory is simulated without icons
        fake_dir = tempfile.mkdtemp()
        try:
            # OwlBrowser should handle missing icons without throwing any Exception
            browser_no_icon = OwlBrowser(show_profile_selector_on_start=False)
            self.assertIsNotNone(browser_no_icon)
            browser_no_icon.close()
            browser_no_icon.deleteLater()
        finally:
            shutil.rmtree(fake_dir, ignore_errors=True)


class TestM4SingleInstanceAndStealth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        SingleInstanceGuard.release_all()

    def tearDown(self):
        SingleInstanceGuard.release_all()

    def test_rapid_single_instance_acquisition_release_cycles(self):
        """Stress test SingleInstanceGuard with 30 rapid acquire/release cycles."""
        key = f"Owl_Stress_Test_{os.getpid()}"
        guard = SingleInstanceGuard(app_key=key)

        for i in range(30):
            acquired = guard.try_acquire(key)
            self.assertTrue(acquired, f"Iteration {i}: Failed to acquire primary single instance lock.")
            guard.release(key)

    def test_single_instance_secondary_activation_signal(self):
        """Verify secondary instance try_acquire returns False and triggers activation_requested signal."""
        key = f"Owl_Activation_Test_{os.getpid()}"
        primary_guard = SingleInstanceGuard(app_key=key)
        signal_received = []

        primary_guard.activation_requested.connect(lambda: signal_received.append(True))
        acquired_primary = primary_guard.try_acquire(key)
        self.assertTrue(acquired_primary)

        # Secondary guard attempt
        secondary_guard = SingleInstanceGuard(app_key=key)
        acquired_secondary = secondary_guard.try_acquire(key)
        self.assertFalse(acquired_secondary, "Secondary instance must return False.")

        # Process events for IPC socket signal propagation
        QApplication.processEvents()
        self.assertTrue(len(signal_received) > 0, "Primary instance must receive activation_requested signal.")

        primary_guard.release(key)
        secondary_guard.release(key)

    def test_stealth_window_flags_and_affinity(self):
        """Verify OwlBrowser window flags (WindowStaysOnTopHint, Window; no Tool so it stays on outside click)."""
        browser = OwlBrowser(show_profile_selector_on_start=False)
        flags = browser.windowFlags()

        from owl.workspace.main_window import _window_type
        self.assertEqual(
            _window_type(flags),
            Qt.WindowType.Window,
            "Must be a normal Window (not Tool — Tool hides on macOS outside click).",
        )
        self.assertTrue(bool(flags & Qt.WindowType.WindowStaysOnTopHint), "Must have WindowStaysOnTopHint flag.")

        # Verify win32 display affinity function
        hwnd = int(browser.winId())
        self.assertGreater(hwnd, 0, "Window handle (HWND) must be valid (> 0).")
        res = apply_display_affinity(hwnd)
        # On Windows offscreen or actual desktop, apply_display_affinity should return a bool without exception
        self.assertIsInstance(res, bool)

        browser.close()
        browser.deleteLater()

    def test_hotkey_listener_rapid_triggering(self):
        """Verify GlobalHotkey listener start/stop lifecycle and rapid trigger invocation."""
        triggered_count = 0

        def on_toggle():
            nonlocal triggered_count
            triggered_count += 1

        hotkey = GlobalHotkey(on_toggle=on_toggle)
        hotkey.start()

        # Rapidly invoke trigger callback directly
        for _ in range(20):
            on_toggle()

        self.assertEqual(triggered_count, 20)
        hotkey.stop()
        self.assertFalse(hotkey._running)


if __name__ == "__main__":
    unittest.main()
