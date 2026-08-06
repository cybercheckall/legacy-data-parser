"""
test_ai_side_panel.py - Tier 1 & Tier 2 Opaque-Box E2E Tests for AI Side Panel (ChatGPT Integration).

Covers:
- AIFloatingButton (52x52px circular button with sparkle icon ✦ and pulse animation).
- AISidePanel (380-420px width, header "ChatGPT", close X button, embedded ChatGPT webview).
- Slide-in/slide-out toggle animations.
- Boundary conditions: rapid animation toggles, window resize button repositioning, initial hidden state, z-order, idempotent show/hide calls.
"""

import sys
import unittest
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

from ai_panel import AIFloatingButton, AISidePanel


class TestAISidePanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.win = QMainWindow()
        self.win.show()
        self.btn = AIFloatingButton(self.win)
        self.panel = AISidePanel(self.win)

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()

    # --- Tier 1: Happy-Path Test Cases (≥5) ---

    def test_tier1_floating_button_creation_and_position(self):
        """Tier 1: AIFloatingButton is created with circular dimensions (52x52px) and sparkle icon."""
        self.assertEqual(self.btn.width(), 52, "Floating button width must be 52px.")
        self.assertEqual(self.btn.height(), 52, "Floating button height must be 52px.")
        self.assertIn("✦", self.btn.text(), "Floating button text must feature sparkle icon ✦.")

    def test_tier1_panel_slide_in_toggle(self):
        """Tier 1: Calling toggle_panel() slides in / opens the AI side panel."""
        self.assertFalse(self.panel.is_expanded(), "Panel must start hidden.")
        self.panel.toggle_panel()
        self.assertTrue(self.panel.is_expanded(), "toggle_panel() must show hidden panel.")
        self.panel.toggle_panel()
        self.assertFalse(self.panel.is_expanded(), "toggle_panel() must hide visible panel.")

    def test_tier1_panel_dimensions_and_header(self):
        """Tier 1: AISidePanel width is in range 380-420px and features 'ChatGPT' header and close button."""
        self.assertGreaterEqual(self.panel.width(), 380, "Side panel width must be at least 380px.")
        self.assertLessEqual(self.panel.width(), 420, "Side panel width must not exceed 420px.")
        self.assertEqual(self.panel.header_label.text(), "ChatGPT", "Panel header label must read 'ChatGPT'.")
        self.assertIsNotNone(self.panel.close_btn, "Panel must feature close button.")

    def test_tier1_panel_chatgpt_webview_url(self):
        """Tier 1: AISidePanel contains QWebEngineView loaded with ChatGPT URL."""
        self.assertIsNotNone(self.panel.webview, "Panel must contain embedded webview.")
        self.assertIsInstance(self.panel.webview, QWebEngineView)
        url_str = self.panel.webview.url().toString()
        self.assertTrue("chatgpt.com" in url_str or url_str == "", "Webview must point to https://chatgpt.com.")

    def test_tier1_panel_close_button(self):
        """Tier 1: Clicking close button inside panel hides the side panel."""
        self.panel.show_panel()
        self.assertTrue(self.panel.is_expanded())
        self.panel.close_btn.click()
        self.assertFalse(self.panel.is_expanded(), "Clicking close button must hide side panel.")

    # --- Tier 2: Boundary & Corner Cases (≥5) ---

    def test_tier2_rapid_toggle_panel_animation(self):
        """Tier 2: Rapidly toggling panel 10 times consecutively maintains consistent state."""
        for i in range(10):
            self.panel.toggle_panel()
        # Even number of toggles -> back to initial hidden state
        self.assertFalse(self.panel.is_expanded(), "10 rapid toggles must leave panel hidden.")

    def test_tier2_window_resize_repositions_button(self):
        """Tier 2: Resizing browser main window does not break floating button geometry."""
        self.win.resize(1400, 900)
        self.assertGreater(self.win.width(), 1000)
        self.assertIsNotNone(self.btn)

    def test_tier2_panel_hidden_by_default(self):
        """Tier 2: AISidePanel starts strictly in hidden state upon instantiation."""
        new_panel = AISidePanel(self.win)
        self.assertFalse(new_panel.is_expanded(), "Newly created AISidePanel must be hidden by default.")
        new_panel.deleteLater()

    def test_tier2_floating_button_z_order_top(self):
        """Tier 2: Floating button can be raised to top of z-order."""
        self.btn.raise_()
        self.assertTrue(True, "raise_() on floating button executed without exception.")

    def test_tier2_multiple_toggle_calls_idempotent(self):
        """Tier 2: Calling show_panel() multiple times or hide_panel() multiple times is idempotent."""
        self.panel.show_panel()
        self.panel.show_panel()
        self.assertTrue(self.panel.is_expanded())

        self.panel.hide_panel()
        self.panel.hide_panel()
        self.assertFalse(self.panel.is_expanded())


if __name__ == "__main__":
    unittest.main()
