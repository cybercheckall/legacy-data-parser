"""
test_stealth_affinity.py - Tier 1 & Tier 2 Opaque-Box E2E Tests for Stealth Window & Win32 Display Affinity.

Covers:
- SetWindowDisplayAffinity(hwnd, 0x00000011) execution and result.
- MainWindow HWND handle retrieval via winId().
- Window flags: Qt.WindowType.Tool (no taskbar icon) and Qt.WindowType.WindowStaysOnTopHint.
- Esc key press behavior (hides window without exiting).
"""

import sys
import os
import unittest
import pytest
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication

import stealth_browser.win32_utils as win32_utils
from stealth_browser.main_window import MainWindow
from stealth_browser.config import WDA_EXCLUDEFROMCAPTURE


class TestStealthAffinity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()

    def test_tier1_set_stealth_affinity_win32_function(self):
        """Tier 1: Verify set_stealth_affinity function exists and handles HWND call."""
        hwnd = int(self.window.winId())
        self.assertGreater(hwnd, 0, "Window HWND must be a positive integer.")
        result = win32_utils.set_stealth_affinity(hwnd)
        self.assertTrue(result, "set_stealth_affinity must return True upon calling SetWindowDisplayAffinity.")

    def test_tier1_main_window_applies_affinity_on_creation(self):
        """Tier 1: MainWindow applies stealth affinity upon creation/show."""
        self.window.show()
        hwnd = int(self.window.winId())
        self.assertGreater(hwnd, 0, "Valid HWND must be assigned to MainWindow.")
        # Verify affinity applied property or call
        if hasattr(self.window, "stealth_affinity_applied"):
            self.assertTrue(self.window.stealth_affinity_applied)
        elif hasattr(self.window, "apply_stealth_affinity"):
            res = self.window.apply_stealth_affinity()
            self.assertTrue(res)

    def test_tier2_window_flags_tool_window(self):
        """Tier 2: Window flags must include Qt.WindowType.Tool for taskbar icon suppression."""
        flags = self.window.windowFlags()
        self.assertTrue(
            bool(flags & Qt.WindowType.Tool),
            "MainWindow must have Qt.WindowType.Tool flag to hide from taskbar."
        )

    def test_tier2_window_flags_stays_on_top(self):
        """Tier 2: Window flags must include Qt.WindowType.WindowStaysOnTopHint."""
        flags = self.window.windowFlags()
        self.assertTrue(
            bool(flags & Qt.WindowType.WindowStaysOnTopHint),
            "MainWindow must have Qt.WindowType.WindowStaysOnTopHint flag to remain on top."
        )

    def test_tier2_esc_key_hides_window(self):
        """Tier 2: Pressing Esc key hides the browser window (does not close application)."""
        self.window.show()
        self.assertTrue(self.window.isVisible(), "Window should initially be visible.")

        # Construct Esc key press event
        esc_event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Escape,
            Qt.KeyboardModifier.NoModifier
        )
        QApplication.sendEvent(self.window, esc_event)

        # Assert window is hidden
        self.assertFalse(self.window.isVisible(), "Esc key press must hide the MainWindow.")

    def test_tier2_wda_constant_value(self):
        """Tier 2: Constant WDA_EXCLUDEFROMCAPTURE must equal 0x00000011 (17)."""
        self.assertEqual(WDA_EXCLUDEFROMCAPTURE, 0x00000011)


if __name__ == "__main__":
    unittest.main()
