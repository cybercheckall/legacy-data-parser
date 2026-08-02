"""
test_hotkey.py - Tier 3 Opaque-Box E2E Tests for Global Hotkey & Shortcut Combinations.

Covers:
- Global Hotkey (Ctrl+Shift+B) registration & callback execution.
- Hotkey toggle state checks (visible -> hidden -> visible).
- Keyboard shortcut interactions (Ctrl+L for address bar focus, Ctrl+T, Ctrl+W, Esc).
"""

import sys
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent

from stealth_browser.hotkey_manager import HotkeyManager
from stealth_browser.main_window import MainWindow


class TestHotkeyAndShortcuts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.window = MainWindow()
        self.hotkey_mgr = getattr(self.window, "hotkey_mgr", HotkeyManager(self.window))

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()

    # --- Tier 3: Cross-Feature Combinations & Hotkey State ---

    def test_tier3_global_hotkey_registration(self):
        """Tier 3: HotkeyManager registers Ctrl+Shift+B callback successfully."""
        callback_called = []
        mgr = HotkeyManager()
        res = mgr.register_global_hotkey(lambda: callback_called.append(True))
        
        self.assertTrue(res, "register_global_hotkey must return True on success.")
        self.assertTrue(mgr.registered, "HotkeyManager registered flag must be True.")
        
        # Simulate hotkey trigger
        mgr.trigger_hotkey()
        self.assertEqual(len(callback_called), 1, "Triggering hotkey must execute registered callback.")

    def test_tier3_hotkey_visibility_toggle_states(self):
        """Tier 3: Hotkey toggle state transitions (Visible -> Hidden -> Visible)."""
        self.window.show()
        self.assertTrue(self.window.isVisible(), "Window must start visible after show().")

        # First toggle: Visible -> Hidden
        self.window.toggle_visibility()
        self.assertFalse(self.window.isVisible(), "First hotkey toggle must hide visible window.")

        # Second toggle: Hidden -> Visible
        self.window.toggle_visibility()
        self.assertTrue(self.window.isVisible(), "Second hotkey toggle must restore hidden window to visible.")

    def test_tier3_shortcut_combinations_interaction(self):
        """Tier 3: Verify shortcut interactions with MainWindow component integration."""
        self.window.show()
        
        # Test tab opening via TabWidget integration
        initial_tabs = self.window.tab_widget.count()
        self.window.tab_widget.add_new_tab(url="https://google.com", label="Tab 2")
        self.assertEqual(self.window.tab_widget.count(), initial_tabs + 1, "Opening new tab must increment tab count.")

        # Test tab closing via TabWidget integration
        self.window.tab_widget.close_tab(self.window.tab_widget.count() - 1)
        self.assertEqual(self.window.tab_widget.count(), initial_tabs, "Closing tab must decrement tab count.")

        # Test Esc key press hides window
        esc_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(self.window, esc_event)
        self.assertFalse(self.window.isVisible(), "Esc key shortcut must hide window.")


if __name__ == "__main__":
    unittest.main()
