"""
test_stealth.py - Tier 1 & Tier 2 Opaque-Box E2E Tests for Stealth Features Preservation.

Covers:
- Win32 SetWindowDisplayAffinity (WDA_EXCLUDEFROMCAPTURE = 0x00000011).
- Window Flags: Qt.WindowType.Tool (no taskbar icon) and Qt.WindowType.WindowStaysOnTopHint (always on top).
- Global Hotkey (Ctrl+Shift+B) registration & visibility toggle.
- Escape key window hiding behavior.
- PyInstaller build spec (phantom_browser.spec).
- Boundary conditions: repeated hotkey toggling, invalid HWND handle, constant hex value validation, spec file validation, initialization property checks.
"""

import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent

from display_affinity import apply_display_affinity, WDA_EXCLUDEFROMCAPTURE
from hotkey import GlobalHotkey, HotkeyManager
from stealth_browser.main_window import MainWindow


class TestStealthFeaturesPreservation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.win = MainWindow()

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()

    # --- Tier 1: Happy-Path Test Cases (≥5) ---

    def test_tier1_display_affinity_exclusion(self):
        """Tier 1: SetWindowDisplayAffinity is executed with WDA_EXCLUDEFROMCAPTURE."""
        hwnd = int(self.win.winId())
        self.assertGreater(hwnd, 0, "Window HWND must be positive integer.")
        res = apply_display_affinity(hwnd)
        self.assertTrue(res, "apply_display_affinity must return True.")

    def test_tier1_tool_window_flag(self):
        """Tier 1: Main window includes Qt.WindowType.Tool flag to suppress taskbar icon."""
        flags = self.win.windowFlags()
        self.assertTrue(
            bool(flags & Qt.WindowType.Tool),
            "Main window must have Qt.WindowType.Tool flag set."
        )

    def test_tier1_stays_on_top_flag(self):
        """Tier 1: Main window includes Qt.WindowType.WindowStaysOnTopHint flag."""
        flags = self.win.windowFlags()
        self.assertTrue(
            bool(flags & Qt.WindowType.WindowStaysOnTopHint),
            "Main window must have Qt.WindowType.WindowStaysOnTopHint flag set."
        )

    def test_tier1_global_hotkey_registered(self):
        """Tier 1: Global hotkey manager registers callback for visibility toggle."""
        called = []
        hk_mgr = HotkeyManager()
        res = hk_mgr.register_global_hotkey(lambda: called.append(True))
        self.assertTrue(res, "register_global_hotkey must return True on registration.")
        self.assertTrue(hk_mgr.registered, "HotkeyManager registered attribute must be True.")
        hk_mgr.trigger_hotkey()
        self.assertEqual(len(called), 1, "Triggering hotkey must execute callback.")

    def test_tier1_esc_key_hides_window(self):
        """Tier 1: Pressing Esc key hides browser window without terminating application."""
        self.win.show()
        self.assertTrue(self.win.isVisible(), "Window must start visible after show().")

        esc_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(self.win, esc_event)

        self.assertFalse(self.win.isVisible(), "Esc key press must hide main window.")

    # --- Tier 2: Boundary & Corner Cases (≥5) ---

    def test_tier2_hotkey_toggle_repeated(self):
        """Tier 2: Rapidly toggling window visibility via hotkey 10 times maintains consistent state."""
        self.win.show()
        self.assertTrue(self.win.isVisible())

        for _ in range(10):
            self.win.toggle_visibility()

        # 10 toggles -> back to initial visible state
        self.assertTrue(self.win.isVisible(), "10 toggles must return window to visible state.")

    def test_tier2_display_affinity_invalid_hwnd(self):
        """Tier 2: Calling apply_display_affinity with 0 or negative HWND handles input safely."""
        res_zero = apply_display_affinity(0)
        res_neg = apply_display_affinity(-1)
        self.assertTrue(isinstance(res_zero, bool))
        self.assertTrue(isinstance(res_neg, bool))

    def test_tier2_wda_constant_hex_value(self):
        """Tier 2: WDA_EXCLUDEFROMCAPTURE constant equals 0x00000011 (decimal 17)."""
        self.assertEqual(WDA_EXCLUDEFROMCAPTURE, 0x00000011)
        self.assertEqual(WDA_EXCLUDEFROMCAPTURE, 17)

    def test_tier2_pyinstaller_spec_validity(self):
        """Tier 2: PyInstaller spec file (owl.spec or phantom_browser.spec) exists and contains build configuration."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        spec_path = os.path.join(project_root, "owl.spec")
        if not os.path.exists(spec_path):
            spec_path = os.path.join(project_root, "phantom_browser.spec")
        self.assertTrue(os.path.exists(spec_path), "owl.spec or phantom_browser.spec file must exist in project root.")
        
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue(len(content) > 0, "PyInstaller spec file must not be empty.")

    def test_tier2_stealth_applied_property(self):
        """Tier 2: stealth_affinity_applied attribute is set to True upon window setup."""
        if hasattr(self.win, "stealth_affinity_applied"):
            self.assertTrue(self.win.stealth_affinity_applied)
        else:
            res = self.win.apply_stealth_affinity()
            self.assertTrue(res)


if __name__ == "__main__":
    unittest.main()
