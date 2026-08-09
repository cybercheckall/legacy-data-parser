"""
test_challenger_m3_it2_deep_stress.py - Empirical Adversarial Stress Test Suite for M3 Remediation.

Covers 5 target areas:
1. AI side panel geometry offsets & TitleBar non-obstruction
2. Slide-out animation transitions & mid-flight reversal
3. ProfileSelector view AI floating button toggling & overlay safety
4. Settings tab closing edge cases (single tab vs multi-tab fallback)
5. Settings sub-page bidirectional UI state synchronization
"""

import sys
import os
import unittest
import tempfile
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QUrl, QRect, QEventLoop, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView

from owl.workspace.main_window import PhantomBrowser, WebTab
from owl.profiles.profile_manager import ProfileManager, Profile
from owl.settings.view import SettingsView
from owl.ai.panel import AISidePanel, AIFloatingButton
from owl.profiles.profile_selector import ProfileSelector


class TestAISidePanelGeometryAndAnimation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "ai_geom_profiles.json")
        self.pm = ProfileManager(json_path=self.json_path)
        self.browser = PhantomBrowser(show_profile_selector_on_start=False)
        self.browser._profile_manager = self.pm
        self.browser.show()
        self.app.processEvents()

    def tearDown(self):
        self.browser.close()
        self.browser.deleteLater()
        self.tmp_dir.cleanup()

    def test_ai_panel_geometry_offset_titlebar_non_obstruction(self):
        """Docked panel sits in content row (below shell) and pushes page width — not an overlay."""
        shell_h = self.browser._shell_height()
        self.assertGreater(shell_h, 0, "Shell height must be > 0")

        panel = self.browser.ai_panel
        page = self.browser.page_column
        page_w_before = page.width()

        panel.show_panel()
        self.app.processEvents()

        loop = QEventLoop()
        panel._anim.finished.connect(loop.quit)
        if panel._anim.state() == panel._anim.State.Running:
            loop.exec()
        self.app.processEvents()

        self.assertTrue(panel.isVisible())
        self.assertGreaterEqual(panel.width(), 380)
        self.assertLessEqual(panel.width(), 420)
        # Panel is parented under content layer — below shell, not covering handler
        top_left = panel.mapTo(self.browser, panel.rect().topLeft())
        self.assertGreaterEqual(top_left.y(), shell_h - 1)
        # Page column is pushed narrower when panel opens
        self.assertLess(page.width(), page_w_before + 1)
        self.assertLess(page.width() + panel.width(), self.browser.width() + 40)

        self.browser.resize(1300, 850)
        self.browser._reposition_ai_components()
        self.app.processEvents()
        self.assertTrue(panel.is_expanded())
        self.assertGreaterEqual(panel.width(), 380)

    def test_ai_panel_slide_out_animation_and_reversal(self):
        """Test width push-in / push-out animation and mid-flight cancellation."""
        panel = self.browser.ai_panel

        # 1. Push-in
        panel.show_panel()
        self.assertTrue(panel.is_expanded())
        self.assertTrue(panel.isVisible())

        loop = QEventLoop()
        panel._anim.finished.connect(loop.quit)
        if panel._anim.state() == panel._anim.State.Running:
            loop.exec()

        self.assertGreaterEqual(panel.width(), 380)

        # 2. Push-out
        panel.hide_panel()
        self.assertFalse(panel.is_expanded())
        self.assertTrue(panel.isVisible(), "Widget must remain visible during slide-out animation.")

        loop2 = QEventLoop()
        panel._anim.finished.connect(loop2.quit)
        if panel._anim.state() == panel._anim.State.Running:
            loop2.exec()

        self.assertFalse(panel.isVisible(), "Widget must hide when slide-out animation finishes.")
        self.assertEqual(panel.width(), 0)

        # 3. Rapid mid-flight reversal
        panel.show_panel()
        self.assertTrue(panel._anim.state() == panel._anim.State.Running)
        panel.hide_panel()
        self.assertFalse(panel.is_expanded())

        loop3 = QEventLoop()
        panel._anim.finished.connect(loop3.quit)
        if panel._anim.state() == panel._anim.State.Running:
            loop3.exec()

        self.assertFalse(panel.isVisible())
        self.assertFalse(panel.is_expanded())


class TestProfileSelectorViewButtonToggling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "ps_toggle_profiles.json")
        self.pm = ProfileManager(json_path=self.json_path)
        self.browser = PhantomBrowser(show_profile_selector_on_start=False)
        self.browser._profile_manager = self.pm
        self.browser.show()
        self.app.processEvents()

    def tearDown(self):
        self.browser.close()
        self.browser.deleteLater()
        self.tmp_dir.cleanup()

    def test_floating_button_visibility_guarded_by_active_view(self):
        """Verify floating button is hidden on ProfileSelector view and visible on Workspace view."""
        btn = self.browser.ai_button

        # 1. Workspace active -> button visible
        self.browser.show_workspace()
        self.app.processEvents()
        self.assertTrue(btn.isVisible(), "AIFloatingButton must be visible in Workspace view.")

        # 2. Switch to ProfileSelector -> button hidden
        self.browser.show_profile_selector()
        self.app.processEvents()
        self.assertFalse(btn.isVisible(), "AIFloatingButton must be hidden in ProfileSelector view.")

        # 3. Resize window while ProfileSelector is active -> button stays hidden
        self.browser.resize(1200, 800)
        self.app.processEvents()
        self.assertFalse(btn.isVisible(), "AIFloatingButton must remain hidden after resize in ProfileSelector view.")

        # 4. Switch back to Workspace -> button visible
        self.browser.show_workspace()
        self.app.processEvents()
        self.assertTrue(btn.isVisible(), "AIFloatingButton must reappear when returning to Workspace view.")

    def test_show_profile_selector_collapses_open_ai_panel(self):
        """Verify calling show_profile_selector() collapses expanded AI panel."""
        panel = self.browser.ai_panel
        self.browser.show_workspace()
        panel.show_panel()
        self.assertTrue(panel.is_expanded())

        self.browser.show_profile_selector()
        self.app.processEvents()

        self.assertFalse(panel.is_expanded(), "AISidePanel must collapse when switching to ProfileSelector.")


class TestSettingsTabClosingEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "settings_close_profiles.json")
        self.pm = ProfileManager(json_path=self.json_path)
        self.browser = PhantomBrowser(show_profile_selector_on_start=False)
        self.browser._profile_manager = self.pm
        self.browser.show()
        self.app.processEvents()

    def tearDown(self):
        self.browser.close()
        self.browser.deleteLater()
        self.tmp_dir.cleanup()

    def test_close_settings_when_sole_remaining_tab(self):
        """Verify closing SettingsView when count() == 1 replaces tab with default homepage WebTab."""
        tab_widget = self.browser.tab_widget

        # Remove initial tabs so count == 0, then open SettingsView
        while tab_widget.count() > 0:
            tab_widget.removeTab(0)

        settings_tab = self.browser._open_settings()
        self.assertEqual(tab_widget.count(), 1)
        self.assertIsInstance(tab_widget.widget(0), SettingsView)

        # Close the sole remaining tab
        tab_widget.close_tab(0)
        self.app.processEvents()

        self.assertEqual(tab_widget.count(), 1, "Tab count must remain 1 on last tab close.")
        new_widget = tab_widget.widget(0)
        self.assertNotIsInstance(new_widget, SettingsView, "SettingsView must be replaced.")
        self.assertIsInstance(new_widget, WebTab, "Replaced tab must be a WebTab instance.")

    def test_close_settings_in_multitab_environment(self):
        """Verify closing SettingsView in multi-tab setup removes SettingsView and retains other tabs."""
        tab_widget = self.browser.tab_widget

        while tab_widget.count() > 0:
            tab_widget.removeTab(0)

        # Create WebTab (idx 0) and SettingsView (idx 1)
        self.browser.add_new_tab("https://www.google.com")
        settings_view = self.browser._open_settings()
        self.assertEqual(tab_widget.count(), 2)

        # Close SettingsView (idx 1)
        tab_widget.close_tab(1)
        self.app.processEvents()

        self.assertEqual(tab_widget.count(), 1)
        self.assertIsInstance(tab_widget.widget(0), WebTab)


class TestSubPageUISynchronization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "subpage_sync_profiles.json")
        self.pm = ProfileManager(json_path=self.json_path)
        self.browser = PhantomBrowser(show_profile_selector_on_start=False)
        self.browser._profile_manager = self.pm
        self.browser.show()
        self.app.processEvents()

    def tearDown(self):
        self.browser.close()
        self.browser.deleteLater()
        self.tmp_dir.cleanup()

    def test_settings_subpage_sync_between_general_profiles_search(self):
        """Verify editing settings in Page 1 (Profiles) updates Page 0 (General) and Page 2 (Search Engine)."""
        settings_view = self.browser._open_settings()

        # 1. In Page 1, update active profile homepage to DDG and search engine to DuckDuckGo
        settings_view.prof_hp_input.setText("https://duckduckgo.com")
        idx_ddg = settings_view.prof_engine_combo.findText("DuckDuckGo")
        settings_view.prof_engine_combo.setCurrentIndex(idx_ddg)
        settings_view._on_save_active_profile()

        # Verify Page 0 (General) homepage_input updated
        self.assertEqual(settings_view.homepage_input.text(), "https://duckduckgo.com")

        # Verify Page 2 (Search Engine) radio buttons updated
        self.assertTrue(settings_view.radio_ddg.isChecked())
        self.assertFalse(settings_view.radio_google.isChecked())

        # 2. Switch radio button in Page 2 to Google
        settings_view.radio_google.setChecked(True)
        self.app.processEvents()

        active = self.pm.get_active_profile()
        self.assertEqual(active.search_engine, "Google")
        self.assertEqual(settings_view.prof_engine_combo.currentText(), "Google")

    def test_create_and_delete_profile_subpage_sync(self):
        """Verify profile creation and deletion syncs sub-pages cleanly."""
        settings_view = self.browser._open_settings()

        # Create new profile
        settings_view.new_prof_name.setText("Dev Profile")
        settings_view.new_prof_hp.setText("https://github.com")
        settings_view.new_prof_engine.setCurrentText("DuckDuckGo")
        settings_view._on_create_profile_clicked()

        profiles = self.pm.load_profiles()
        dev_prof = [p for p in profiles if p.name == "Dev Profile"][0]

        # Make Dev Profile active
        idx = settings_view.prof_select_combo.findData(dev_prof.id)
        settings_view.prof_select_combo.setCurrentIndex(idx)
        settings_view._on_set_active_profile_clicked()

        # Sub-pages must reflect Dev Profile settings
        self.assertEqual(settings_view.homepage_input.text(), "https://github.com")
        self.assertTrue(settings_view.radio_ddg.isChecked())


if __name__ == "__main__":
    unittest.main()
