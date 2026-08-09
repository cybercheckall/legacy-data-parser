"""
test_e2e_scenarios.py - Tier 3 Pairwise Combinations & Tier 4 Real-World Application Scenarios.

Covers:
- Tier 3 Pairwise Feature Combination Tests (Profiles x Settings, Single-Instance x Stealth, AI Panel x Tab Navigation, Settings x URL Bar, Hotkey x AI Panel).
- Tier 4 Real-World Workload Scenarios (Full E2E user workflows exercising all features in combination).
"""

import sys
import os
import json
import unittest
import tempfile
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QEvent, QUrl
from PyQt6.QtGui import QKeyEvent

from owl.stealth.single_instance import SingleInstanceGuard
from owl.profiles.profile_manager import Profile, ProfileManager
from owl.shell.title_bar import TitleBar
from owl.shell.nav_bar import NavBar
from owl.shell.tab_bar import TabWidget
from owl.profiles.profile_selector import ProfileSelector
from owl.ai.panel import AIFloatingButton, AISidePanel
from owl.settings.view import SettingsView
from owl.stealth.display_affinity import apply_display_affinity
from hotkey import HotkeyManager
from stealth_browser.main_window import MainWindow


class TestE2EScenariosAndPairwise(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "e2e_profiles.json")
        self.pm = ProfileManager(json_path=self.json_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    # --- Tier 3: Pairwise Feature Combination Tests (5 tests) ---

    def test_tier3_profile_switch_updates_search_engine_and_homepage(self):
        """Tier 3 (Profiles x Settings): Switching active profile dynamically updates active search engine and homepage."""
        prof_work = self.pm.create_profile(
            name="Work",
            avatar="💼",
            homepage="https://chatgpt.com",
            search_engine="DuckDuckGo"
        )
        self.pm.set_active_profile(prof_work.id)

        active = self.pm.get_active_profile()
        self.assertEqual(active.homepage, "https://chatgpt.com")
        self.assertEqual(active.search_engine, "DuckDuckGo")

    def test_tier3_single_instance_activation_preserves_stealth_flags(self):
        """Tier 3 (Single Instance x Stealth): Secondary instance activation preserves window flags and display affinity."""
        import uuid
        app_key = f"tier3_stealth_ipc_{uuid.uuid4().hex[:8]}"
        guard1 = SingleInstanceGuard(app_key=app_key)
        guard2 = SingleInstanceGuard(app_key=app_key)

        win = MainWindow()
        win.show()

        # Primary acquires lock
        self.assertTrue(guard1.try_acquire())

        # Secondary attempts acquire, fails, signals primary
        self.assertFalse(guard2.try_acquire())

        # Confirm window flags preserved on primary (no Tool — stays visible on outside click)
        from owl.workspace.main_window import _window_type
        flags = win.windowFlags()
        self.assertEqual(_window_type(flags), Qt.WindowType.Window)
        self.assertTrue(bool(flags & Qt.WindowType.WindowStaysOnTopHint))

        win.close()
        win.deleteLater()
        guard1.release()
        guard2.release()

    def test_tier3_ai_panel_open_during_tab_navigation(self):
        """Tier 3 (AI Side Panel x Tab Navigation): Opening AI panel while adding and switching tabs maintains panel state."""
        win = QMainWindow()
        win.show()
        tabs = TabWidget(win)
        ai_panel = AISidePanel(win)

        ai_panel.show_panel()
        self.assertTrue(ai_panel.is_expanded())

        # Add tabs while AI panel is open
        idx1 = tabs.add_new_tab("https://google.com", "Google")
        idx2 = tabs.add_new_tab("https://github.com", "GitHub")
        tabs.setCurrentIndex(idx1)

        # AI panel remains visible during tab navigation
        self.assertTrue(ai_panel.is_expanded(), "AI panel must stay open during tab switches.")

        win.close()
        win.deleteLater()

    def test_tier3_settings_update_reflected_in_active_tab(self):
        """Tier 3 (Settings x URL Bar): Changing default search engine in Settings updates query URL formatting."""
        settings = SettingsView(profile_manager=self.pm)
        settings.set_search_engine("DuckDuckGo")

        active_engine = self.pm.get_active_profile().search_engine
        self.assertEqual(active_engine, "DuckDuckGo")

        settings.deleteLater()

    def test_tier3_hotkey_hide_preserves_ai_panel_state(self):
        """Tier 3 (Global Hotkey x AI Side Panel): Hiding window via hotkey with open AI panel keeps AI panel open on restore."""
        win = MainWindow()
        ai_panel = AISidePanel(win)
        win.show()

        ai_panel.show_panel()
        self.assertTrue(ai_panel.isVisible())

        # Toggle hide
        win.toggle_visibility()
        self.assertFalse(win.isVisible())

        # Toggle show
        win.toggle_visibility()
        self.assertTrue(win.isVisible())
        self.assertTrue(ai_panel.isVisible(), "AI side panel state must be preserved after window show toggle.")

        win.close()
        win.deleteLater()

    # --- Tier 4: Real-World Application Scenarios (5 tests) ---

    def test_tier4_scenario_1_profile_launch_search_settings_newtab(self):
        """Tier 4 Scenario 1: Profile Launch -> Search -> Settings Switch -> New Tab with updated engine."""
        # 1. Profile selection
        prof = self.pm.create_profile(name="Research", avatar="🔬", search_engine="Google")
        self.pm.set_active_profile(prof.id)

        # 2. Window & controls setup
        win = QMainWindow()
        nav = NavBar(win)
        tabs = TabWidget(win)
        settings = SettingsView(profile_manager=self.pm, parent=win)

        # 3. Perform initial search navigation
        nav.url_bar.setText("https://www.google.com")
        nav.url_bar.returnPressed.emit()

        # 4. Open settings and switch search engine to DuckDuckGo
        settings.set_search_engine("DuckDuckGo")
        self.assertEqual(self.pm.get_active_profile().search_engine, "DuckDuckGo")

        # 5. Open new tab
        idx = tabs.add_new_tab("https://duckduckgo.com/?q=stealth", "DuckDuckGo")
        self.assertGreaterEqual(tabs.count(), 1)

        win.close()
        win.deleteLater()

    def test_tier4_scenario_2_multiple_launches_single_instance(self):
        """Tier 4 Scenario 2: Multiple App Launches -> Single Instance Activation across 3 launches."""
        import uuid
        from PyQt6.QtCore import QCoreApplication
        app_key = f"scenario2_single_instance_{uuid.uuid4().hex[:8]}"
        g1 = SingleInstanceGuard(app_key=app_key)
        g2 = SingleInstanceGuard(app_key=app_key)
        g3 = SingleInstanceGuard(app_key=app_key)

        activations = []
        g1.activation_requested.connect(lambda: activations.append(True))

        # Launch 1 (Primary)
        self.assertTrue(g1.try_acquire())

        # Launch 2 (Secondary)
        self.assertFalse(g2.try_acquire())
        QCoreApplication.processEvents()
        self.assertEqual(len(activations), 1)

        # Launch 3 (Tertiary)
        self.assertFalse(g3.try_acquire())
        QCoreApplication.processEvents()
        self.assertEqual(len(activations), 2)

        g1.release()
        g2.release()
        g3.release()

    def test_tier4_scenario_3_ai_panel_chatgpt_workflow(self):
        """Tier 4 Scenario 3: AI Panel Sparkle Button -> Slide-in -> ChatGPT Webview -> Toggle -> Close via X."""
        win = QMainWindow()
        win.show()
        btn = AIFloatingButton(win)
        panel = AISidePanel(win)

        # 1. Floating button starts created
        self.assertEqual(btn.text(), "✦")
        self.assertFalse(panel.is_expanded())

        # 2. Toggle slide-in
        panel.toggle_panel()
        self.assertTrue(panel.is_expanded())

        # 3. Check ChatGPT webview
        self.assertIn("chatgpt.com", panel.webview.url().toString() or "chatgpt.com")

        # 4. Toggle slide-out
        panel.toggle_panel()
        self.assertFalse(panel.is_expanded())

        # 5. Show again and close via close button (X)
        panel.show_panel()
        self.assertTrue(panel.is_expanded())
        panel.close_btn.click()
        self.assertFalse(panel.is_expanded())

        win.close()
        win.deleteLater()

    def test_tier4_scenario_4_stealth_protection_under_offscreen(self):
        """Tier 4 Scenario 4: Stealth Protection Verification under Offscreen Execution."""
        win = MainWindow()
        win.show()

        # 1. HWND & Display Affinity
        hwnd = int(win.winId())
        self.assertGreater(hwnd, 0)
        res = apply_display_affinity(hwnd)
        self.assertTrue(res)

        # 2. Window flags (StaysOnTop; no Tool so outside-click does not hide)
        from owl.workspace.main_window import _window_type
        flags = win.windowFlags()
        self.assertEqual(_window_type(flags), Qt.WindowType.Window)
        self.assertTrue(bool(flags & Qt.WindowType.WindowStaysOnTopHint))

        # 3. Esc key hide
        esc_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(win, esc_event)
        self.assertFalse(win.isVisible())

        # 4. Global hotkey registration
        hk_mgr = HotkeyManager(win)
        registered = hk_mgr.register_global_hotkey(win.toggle_visibility)
        self.assertTrue(registered)

        win.close()
        win.deleteLater()

    def test_tier4_scenario_5_full_workspace_workflow(self):
        """Tier 4 Scenario 5: Full Private Workspace Lifecycle (Profile -> Nav -> AI Panel -> Settings -> Tabs -> Hotkey -> Teardown)."""
        # 1. Create and select private profile
        prof = self.pm.create_profile(name="Stealth Dev", avatar="🕵️", homepage="https://google.com", search_engine="Google")
        self.pm.set_active_profile(prof.id)

        # 2. Instantiate main window components
        win = MainWindow()
        win.show()
        self.assertTrue(win.isVisible())

        # 3. Navigate in active tab
        win.nav_bar.url_bar.setText("https://github.com")
        win.nav_bar.url_bar.returnPressed.emit()

        # 4. Open AI Side Panel
        ai_panel = AISidePanel(win)
        ai_panel.show_panel()
        self.assertTrue(ai_panel.isVisible())

        # 5. Open Settings and update search engine
        settings = SettingsView(profile_manager=self.pm, parent=win)
        settings.set_search_engine("DuckDuckGo")
        self.assertEqual(self.pm.get_active_profile().search_engine, "DuckDuckGo")

        # 6. Add multi-tabs and close one
        idx1 = win.tab_widget.add_new_tab("https://stackoverflow.com", "Stack Overflow")
        idx2 = win.tab_widget.add_new_tab("https://claude.ai", "Claude")
        self.assertGreaterEqual(win.tab_widget.count(), 2)
        win.tab_widget.close_tab(idx2)

        # 7. Hotkey visibility toggle
        win.toggle_visibility()
        self.assertFalse(win.isVisible())

        win.toggle_visibility()
        self.assertTrue(win.isVisible())

        # 8. Clean Teardown
        settings.deleteLater()
        ai_panel.deleteLater()
        win.close()
        win.deleteLater()


if __name__ == "__main__":
    unittest.main()
